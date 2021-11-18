import re
from datetime import datetime
from typing import List, Tuple

from aiohttp import ClientSession

BASE_URL = "https://online.vaasansahko.fi"


class Client:
    def __init__(
        self,
        session: ClientSession,
        email: str,
        password: str,
        customer_code: str,
        metering_point_code: str,
        source_company_code: str,
    ) -> None:
        self._session = session
        self._email = email
        self._password = password
        self._customer_code = customer_code
        self._metering_point_code = metering_point_code
        self._source_company_code = source_company_code

    async def login(self) -> None:
        index_url = "{}/eServices/Online/IndexNoAuth".format(BASE_URL)

        async with self._session.get(index_url) as response:
            html = await response.text()

        token = re.findall(
            r'<input name="__RequestVerificationToken" type="hidden" value="(.*)" \/>',
            html,
        )[0]

        login_url = "{}/eServices/Online/Login".format(BASE_URL)
        body = {
            "__RequestVerificationToken": token,
            "UserName": self._email,
            "Password": self._password,
        }

        await self._session.post(login_url, data=body)

    def _fix_timestamp(self, datapoint: Tuple[int, float]) -> Tuple[int, float]:
        dt = int(datetime.utcfromtimestamp(datapoint[0] / 1000).timestamp() * 1000)

        return int(dt), datapoint[1]

    async def get_consumption(self) -> List[Tuple[int, float]]:
        url = "{}/Reporting/CustomerConsumption/GetHourlyConsumption".format(BASE_URL)
        body = {
            "customerCode": self._customer_code,
            "networkCode": "VS0000",
            "meteringPointCode": self._metering_point_code,
            "enableTemperature": False,
            "enablePriceSeries": False,
            "enableTemperatureCorrectedConsumption": False,
            "mpSourceCompanyCode": self._source_company_code,
            "activeTarificationId": "",
        }

        async with self._session.post(url, data=body) as response:
            json = await response.json()

        hourly_consumption = map(
            self._fix_timestamp, json["Consumptions"][0]["Series"]["Data"]
        )

        return list(hourly_consumption)
