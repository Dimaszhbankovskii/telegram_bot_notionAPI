import aiohttp
import json


def get_request_operator():
    return RequestOperator()


class RequestOperator:

    @staticmethod
    async def get_request_response_data(url: str, headers: dict, data: dict | None = None) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url,
                                   data=data,
                                   headers=headers) as resp:
                if resp.status == 200:
                    resp_body: dict = await resp.json()
                    return resp_body
                else:
                    raise Exception(f'Error GET request, status = {resp.status}')

    @staticmethod
    async def post_request_response_data(url: str, headers: dict, data: dict | None = None) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url,
                                    data=json.dumps(data),
                                    headers=headers) as resp:
                if resp.status == 200:
                    resp_body: dict = await resp.json()
                    return resp_body
                else:
                    raise Exception(f'Error POST request, status = {resp.status}, {resp.reason}')
