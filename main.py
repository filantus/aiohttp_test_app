from aiohttp import web
import json
import yaml
from yaml.scanner import ScannerError
from yaml.parser import ParserError
from docker_manager import DockerManager


class BaseView(web.View):
    allowed_methods = ['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH']
    content_type = 'application/json'

    async def get_response(self, request):
        raise Exception('GET method not implemented')

    async def post_response(self, request):
        raise Exception('POST method not implemented')

    def response_405(self):
        data = {
            'error': f'method not allowed',
            'allowed_methods': self.allowed_methods,
        }
        return web.Response(text=json.dumps(data), status=405)

    async def get(self):
        if 'GET' in self.allowed_methods:
            response = await self.get_response(self.request)
            response.content_type = self.content_type
            return response
        return self.response_405()

    async def post(self):
        if 'POST' in self.allowed_methods:
            response = await self.post_response(self.request)
            response.content_type = self.content_type
            return response
        return self.response_405()


class IndexView(BaseView):
    allowed_methods = ['GET']

    async def get_response(self, request):
        data = {'status': 'success'}
        return web.Response(text=json.dumps(data))


class ContainersView(BaseView):
    allowed_methods = ['GET', 'POST']

    async def get_response(self, request):
        return web.Response(text=json.dumps(DockerManager.get_containers()))

    async def post_response(self, request):
        data = await request.read()

        try:
            config = yaml.load(data)
        except (ParserError, ScannerError):
            data = {
                'status': 'failed',
                'error': 'invalid run parameters',
            }
            return web.Response(text=json.dumps(data), status=500)

        try:
            data = {
                'status': 'success',
                'container': DockerManager.run_container(config)
            }
            return web.Response(text=json.dumps(data), status=201)
        except Exception as e:
            data = {
                'status': 'failed',
                'error': str(e),
            }
            return web.Response(text=json.dumps(data), status=500)


class GetContainerView(BaseView):
    allowed_methods = ['GET']

    async def get_response(self, request):
        container = DockerManager.get_container(request.match_info['name'])
        if container:
            return web.Response(text=json.dumps(container))
        return web.Response(text=json.dumps({'error': 'not_found'}), status=404)


class StartContainerView(BaseView):
    allowed_methods = ['POST']

    async def post_response(self, request):
        result = bool(DockerManager.start_container(request.match_info['name']))
        return web.Response(text=json.dumps({'status': 'success' if result else 'failed'}))


class StopContainerView(BaseView):
    allowed_methods = ['POST']

    async def post_response(self, request):
        result = bool(DockerManager.stop_container(request.match_info['name']))
        return web.Response(text=json.dumps({'status': 'success' if result else 'failed'}))


class RemoveContainerView(BaseView):
    allowed_methods = ['POST']

    async def post_response(self, request):
        result = bool(DockerManager.remove_container(request.match_info['name']))
        return web.Response(text=json.dumps({'status': 'success' if result else 'failed'}))


def get_app():
    app = web.Application(middlewares=[
        web.normalize_path_middleware(append_slash=True, merge_slashes=True)])
    app.router.add_get('/', IndexView)
    app.router.add_get('/containers/', ContainersView)
    app.router.add_post('/containers/', ContainersView)
    app.router.add_get('/containers/{name}/', GetContainerView)
    app.router.add_post('/containers/{name}/start/', StartContainerView)
    app.router.add_post('/containers/{name}/stop/', StopContainerView)
    app.router.add_post('/containers/{name}/remove/', RemoveContainerView)
    return app


if __name__ == '__main__':
    try:
        web.run_app(get_app())
    except KeyboardInterrupt:
        pass
    finally:
        DockerManager.client.close()
        print('Exit. Bye-bye!')