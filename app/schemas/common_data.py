from common import creds_notion_api


class CommonData:
    """
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(CommonData, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.url_search = creds_notion_api.search_path
        self.mandatory_headers = {'Authorization': creds_notion_api.authorization_header,
                                  'Notion-Version': creds_notion_api.version}
        self.content_json_header = {'Content-Type': 'application/json'}


common_data_notion: CommonData = CommonData()
