import json
from pathlib import Path
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

vendor_dir = Path(__file__).resolve().parent / "vendor"
if vendor_dir.exists():
    sys.path.append(str(vendor_dir))

from goofish_apis import XianyuApis
from utils.goofish_utils import generate_device_id, trans_cookies


COOKIE_STR = (
    "cna=21FCIsebDnQCAXj2AoZoP+uz; t=9370e0f1d65e875b4993d5fbc8919ba2; "
    "tracknick=you748812; mtop_partitioned_detect=1; "
    "_m_h5_tk=5a52969adbcf8cd88da4d7dd054e3230_1779273753073; "
    "_m_h5_tk_enc=e61a99b1336c33cc6858ad242029d9fc; xlly_s=1; unb=3286898822; "
    "cookie2=23e1178f9ef50eaa02dddd1380f93b2c; _samesite_flag_=true; "
    "_tb_token_=ef659fb3e7b38; sdkSilent=1779352581116; "
    "sgcookie=E100yDv4tFdSFxR5dE5Hm6lXfexVANPpN0XpzKsjI7dHDhSWFNIfWom5bv5aI4zOYdz6DyjKgUuqIbEUjteT2VttBKvwvqysfo9DpKNaIcjozjY%3D; "
    "csg=2f959a1e; "
    "havana_lgc2_77=eyJoaWQiOjMyODY4OTg4MjIsInNnIjoiMjc0MTM1ZDNiNjI3ODNlMzgzNTcwYjQ0OTQyZWIxNTciLCJzaXRlIjo3NywidG9rZW4iOiIxaHJJYm9tMFRkZ3B1V1NnNzBkaWdkQSJ9; "
    "_hvn_lgc_=77; havana_lgc_exp=1781858328293; "
    "tfstk=gqmqhmXErnKquMAnLvqw8c3PatEYflRB7cN_IADghSVcci1izXc8GVgbGOursbUbiS9YbPciifz9H5Ng_fMilLtBAxHYXlVwOHtQ4TqHSVygIZvgr-Zan_3sudMYXlA5FGYBYxh44i_0SlvzqRy0nl2gSYvzCRQgjS4GZa23Z5qisrDkqJecn5VcjuvzB7VgjlcgqLy_Z5qgjfDoMhoicgP4oKwktq3OM6a0txVPjMWLnrvthNsOX0y4ucD0a-yq4-z4tP8B6xmmNAmjDzLdRlHS8fuiZ3Sq_x0nsSiktGPsJ7aomfxdL7mqQ0zxPsb0LoP4-m4l3ikzS4ozcmAOJYMziyrSPUdb5olqJWUDyQhZUSGi0zf2N5gIFm4rtQsr6Pumg8qh4y5TEK3SXq5G7r28UW9yUUa0sCkEkoTNWNUze8PBLp7OWroRfZoEvNQTrOyzOKih."
)


class XianyuSearchTester:
    def __init__(self, cookies_str: str = COOKIE_STR):
        self.cookies = trans_cookies(cookies_str)
        self.api = XianyuApis(
            self.cookies,
            generate_device_id(self.cookies.get("unb", "")),
        )

    def search(self, keyword: str = "545", page_number: int = 1):
        return self.api.search_items(keyword, page_number=page_number)

    def print_search(self, keyword: str = "545", page_number: int = 1):
        result = self.search(keyword, page_number)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result


if __name__ == "__main__":
    keyword = sys.argv[1] if len(sys.argv) > 1 else "iphone"
    page_number = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    XianyuSearchTester().print_search("iphone17 pro", page_number)
