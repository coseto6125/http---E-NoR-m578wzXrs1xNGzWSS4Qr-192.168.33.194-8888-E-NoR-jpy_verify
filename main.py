import pygrab as requests
from pandas import DataFrame, to_numeric


class SignIn:

    def __init__(self):
        self.url = "https://icafe-ht.orz16.com/api/api/"
        self.session = requests.Session()

    def login(self):
        response = self.session.post(
            f"{self.url}/admin/signin",
            data={"username": "admin", "password": "admin1qaz2wsx", "timeZone": "Asia/Taipei", "lang": "zh-cn"},
        )
        response = self.session.get(f"{self.url}/admin/session")
        response = self.session.get(f"{self.url}/channelWallet/order/review/awaiting/count")
        return response

    def get_acc_order(self):  # 會員帳變紀錄
        response = self.session.get(
            f"{self.url}/operations/walletLedgers?pageSize=5000000&currentPage=1&sortBy="
        ).json()
        assert response["codeNO"] == 0, "無法獲取會員帳變紀錄."
        data = DataFrame(response["body"]["rows"]).assign(
            profit=lambda df: to_numeric(df["profit"].str.replace(",", ""))
        )

        data2 = data.query('type.isin(["系统上分", "系统下分"])')
        data = data.query('~type.isin(["系统上分", "系统下分"])')

        return data, data2

    def get_wallet_ledger_type_list(self):  # 注單明細
        response = self.session.get(
            f"{self.url}/operations/gameBetsDetail?pageSize=500000&currentPage=1&sortBy=&sort="
        ).json()
        assert response["codeNO"] == 0, "無法獲取錢包分類帳類型列表."
        data = DataFrame(response["body"]["rows"])
        data["profit"] = to_numeric(data["money"].str.replace(",", ""))
        return data

    def get_game_order(self):  # 交易明細
        # url = lambda x: f"{self.url}/operations/gameBetsOrder?pageSize=10&currentPage=1&sortBy=&sort=&gameUserNo={x}"
        # url_list = map(url,game_user_no)
        # resp = self.session.get_async(url_list)
        # data = {i.rsplit("=",1)[-1]:v.json() for i,v in resp.items()}
        response = self.session.get(
            f"{self.url}/operations/gameBetsOrder?pageSize=500000&currentPage=1&sortBy=&sort="
        ).json()
        assert response["codeNO"] == 0, "無法獲取交易明細."
        data = DataFrame(response["body"]["rows"])
        data["profit"] = to_numeric(data["money"].str.replace(",", ""))
        return data

    def get_daily_report(self):  # 財務報表
        response = self.session.get(f"{self.url}/operations/dailyReportAll?pageSize=500000&currentPage=1").json()
        assert response["codeNO"] == 0, "無法獲取財務報表."
        return DataFrame(response["body"]["rows"])

    def get_channel_ledgers(self):  # 代理帳變明細
        response = self.session.get(
            f"{self.url}/operations/channelLedgers?pageSize=500000&currentPage=1&sortBy=&sort="
        ).json()
        assert response["codeNO"] == 0, "無法獲取代理帳變明細."
        return DataFrame(response["body"]["rows"])


def verify_acc_agent():
    """
    列出不同
    merged = df1.merge(df2, indicator=True, how='outer')
    diff = merged[merged['_merge'] != 'both']
    """
    df_acc_sum1 = df_acc_order.groupby("username")["profit"].sum()
    df_acc_sum2 = df_game_order.groupby("username")["profit"].sum()
    df_acc_sum3 = df_wallet_ledger.groupby("username")["profit"].sum()
    is_equal = df_acc_sum1.equals(df_acc_sum2) and df_acc_sum2.equals(df_acc_sum3)
    assert is_equal, "會員帳變與交易明細不符."

    df_agent_sum1 = df_acc_order.groupby("channelName")["profit"].sum()
    df_agent_sum2 = df_game_order.groupby("channelName")["profit"].sum()
    df_agent_sum3 = df_wallet_ledger.groupby("channelName")["profit"].sum()
    is_equal = df_agent_sum1.equals(df_agent_sum2) and df_agent_sum2.equals(df_agent_sum3)
    assert is_equal, "代理帳變與交易明細不符."

    def calculate(row):
        first_row = row.iloc[0]
        last_row = row.iloc[-1]
        to_num = lambda x: to_numeric(x.replace(",", ""))
        return to_num(first_row["afterMoney"]) - to_num(last_row["originMoney"]) - row["profit"].sum()

    result = df_wallet_ledger.groupby("username").apply(calculate).to_dict()
    for k, v in result.items():
        assert v == 0, f"會員{k}錢包帳變不符.差額為{v}"

    result = df_wallet_ledger.groupby("username").apply(calculate).to_dict()
    for k, v in result.items():
        assert v == 0, f"會員{k}錢包帳變不符.差額為{v}"

    print("finish verify_acc_agent")


method = SignIn()
response = method.login()
df_acc_order, df_sys_order = method.get_acc_order()
df_game_order = method.get_game_order()
df_wallet_ledger = method.get_wallet_ledger_type_list()
df_daily_report = method.get_daily_report()
df_channel_ledgers = method.get_channel_ledgers()
verify_acc_agent()

print(f"總筆數：{df_wallet_ledger['channelName'].count()}")
print("時間固定為預設時間，應為當日 00:00 ~ 23:59")
