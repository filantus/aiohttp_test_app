import docker
from docker.models.containers import Container


class DockerManager:
    client = docker.from_env()

    @classmethod
    def serialize_container(cls, container: Container) -> dict:
        container_data = {}
        for key in ('name', 'status'):
            container_data[key] = getattr(container, key)

        container_data['image'] = container.image.tags[-1]
        container_data['created_at'] = container.attrs.get('Created')
        container_data['started_at'] = container.attrs.get('State', {}).get('StartedAt')
        ports = container.attrs.get('HostConfig', {}).get('PortBindings')
        if ports:
            ports = {k.replace('/tcp', ''): ports[k][0].get('HostPort') for k in ports}
        container_data['ports'] = ports

        return container_data

    @classmethod
    def get_containers(cls, all: bool=True, filters: dict=None) -> list:
        data = []
        for container in cls.client.containers.list(all=all, filters=filters):
            data.append(cls.serialize_container(container))

        return data

    @classmethod
    def get_container(cls, name) -> dict:
        for container in cls.get_containers(filters={'name': name}):
            if container.get('name') == name:
                return container

    @classmethod
    def get_native_container(cls, name) -> Container:
        return (lambda l: l[0] if l else None)(cls.client.containers.list(all=all, filters={'name': name}))

    @classmethod
    def run_container(cls, config):
        for name, params in config.items():
            params = params.get('properties')
            if not params:
                continue

            image = params.get('image')
            if image and not image.endswith(':latest'):
                image += ':latest'

            ports = params.get('ports') or params.get('port_bindings')
            ports = {tuple(d.keys())[0]: tuple(d.values())[0] for d in ports} if ports else None

            container = DockerManager.client.containers.run(
                name=name,
                image=image,
                ports=ports,
                command=params.get('command'),
                detach=True
            )
            return cls.serialize_container(container)

    @classmethod
    def start_container(cls, name):
        container = cls.get_native_container(name)
        if container and container.attrs.get('State').get('Running') is False:
            container.start()
            return True

    @classmethod
    def stop_container(cls, name):
        container = cls.get_native_container(name)
        if container and container.attrs.get('State').get('Running') is True:
            container.stop()
            return True

    @classmethod
    def remove_container(cls, name):
        container = cls.get_native_container(name)
        if container:
            if container.attrs.get('State').get('Running') is True:
                container.stop()
            container.remove()
            return True
