from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
import yaml
from main import get_app
from docker_manager import DockerManager


class AppTestCase(AioHTTPTestCase):
    test_container_name = 'apache-class-test-container'

    async def get_application(self):
        return get_app()

    @staticmethod
    def get_config(override_name=None, ports='56777:56777', parse=False):
        with open('./tests_container_run_parameters.yaml') as f:
            config = f.read()
            if override_name:
                config = config.replace('apache', override_name)
            if ports:
                ports = ports.split(':')
                config = config.replace('- 8080: 80', f'- {ports[0]}: {ports[1]}')
            if parse:
                config = yaml.load(config)
            return config

    @classmethod
    def setUpClass(cls):
        """Run once to set up non-modified data for all class methods."""
        print('#'*100, f'\nsetUpTestData {__name__}...\n', sep='')
        DockerManager.remove_container(cls.test_container_name)
        DockerManager.run_container(cls.get_config(cls.test_container_name, parse=True))

    @classmethod
    def tearDownClass(cls):
        """Run once after all test methods"""
        print('\ntearDownClass...')
        DockerManager.remove_container(cls.test_container_name)
        super().tearDownClass()

    def setUp(self):
        """Run before every test method"""
        print(f'\nTest: {self._testMethodName}...')
        super().setUp()

    def tearDown(self):
        """Run after every test method"""
        super().tearDown()

    @unittest_run_loop
    async def test_index(self):
        resp = await self.client.request('GET', '/')
        assert resp.status == 200
        data = await resp.json()
        assert data is not None

    @unittest_run_loop
    async def test_run_container(self):
        container_name = 'apache-test-run-container'
        DockerManager.remove_container(container_name)

        data = self.get_config(container_name, ports='56778:56778')
        resp = await self.client.request('POST', '/containers/', data=data)

        assert resp.status == 201
        data = await resp.json()
        print(data)
        assert isinstance(data, dict)
        assert data['status'] == 'success'
        assert data['container']['name'] == container_name
        assert data['container']['image'] == 'httpd:latest'

        DockerManager.remove_container(container_name)

    @unittest_run_loop
    async def test_get_containers_list(self):
        resp = await self.client.request('GET', '/containers/')
        assert resp.status == 200
        data = await resp.json()
        print(data)
        assert isinstance(data, list)
        assert data[0]['name'] == 'apache-class-test-container'
        assert data[0]['status'] == 'running'

    @unittest_run_loop
    async def test_get_container(self):
        resp = await self.client.request('GET', f'/containers/{self.test_container_name}')
        assert resp.status == 200
        data = await resp.json()
        print(data)
        assert isinstance(data, dict)
        assert data['name'] == 'apache-class-test-container'
        assert data['status'] == 'running'

    @unittest_run_loop
    async def test_stop_container(self):
        container_name = 'apache-test-stop-container'
        DockerManager.remove_container(container_name)
        DockerManager.run_container(self.get_config(container_name, ports='56779:56779', parse=True))

        resp = await self.client.request('POST', f'/containers/{container_name}/stop/')
        assert resp.status == 200
        data = await resp.json()
        print(data)
        assert isinstance(data, dict)
        assert data['status'] == 'success'

        DockerManager.remove_container(container_name)

    @unittest_run_loop
    async def test_start_container(self):
        container_name = 'apache-test-start-container'
        DockerManager.remove_container(container_name)
        DockerManager.run_container(self.get_config(container_name, ports='56783:56783', parse=True))
        DockerManager.stop_container(container_name)

        resp = await self.client.request('POST', f'/containers/{container_name}/start/')
        assert resp.status == 200
        data = await resp.json()
        print(data)
        assert isinstance(data, dict)
        assert data['status'] == 'success'

        DockerManager.remove_container(container_name)

    @unittest_run_loop
    async def test_remove_container(self):
        container_name = 'apache-test-remove-container'
        DockerManager.remove_container(container_name)
        DockerManager.run_container(self.get_config(container_name, ports='56784:56784', parse=True))

        resp = await self.client.request('POST', f'/containers/{container_name}/remove/')
        assert resp.status == 200
        data = await resp.json()
        print(data)
        assert isinstance(data, dict)
        assert data['status'] == 'success'

        DockerManager.remove_container(container_name)
