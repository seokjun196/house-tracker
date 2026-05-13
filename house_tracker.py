import requests
import os
from datetime import datetime

PUBLIC_DATA_API_KEY = os.environ.get("PUBLIC_DATA_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# 서울 25개 구 코드
SEOUL_DISTRICTS = {
    "강남구": "11680", "강동구": "11740", "강북구": "11305",
    "강서구": "11500", "관악구": "11620", "광진구": "11215",
    "구로구": "11530", "금천구": "11545", "노원구": "11350",
    "도봉구": "11320", "동대문구": "11230", "동작구": "11590",
    "마포구": "11440", "서대문구": "11410", "서초구": "11650",
    "성동구": "11200", "성북구": "11290", "송파구": "11710",
    "양천구": "11470", "영등포구": "11560", "용산구": "11170",
    "은평구": "11380", "종로구": "11110", "중구": "11140",
    "중랑구": "11260"
}


def get_apt_trades(district_code, yyyymm):
    """국토교통부 아파트 매매 실거래가 조회"""
    url = "http://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"
    params = {
        "serviceKey": PUBLIC_DATA_API_KEY,
        "pageNo": 1,
        "numOfRows": 10,
        "LAWD_CD": district_code,
        "DEAL_YMD": yyyymm,
        "dataType": "JSON"
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        if isinstance(items, dict):
            items = [items]
        return items
    except Exception as e:
        print(f"[오류] {district_code}: {e}")
        print(f"[응답 내용]: {res.text[:200]}")
        return []


def get_subscription_info():
    """청약홈 분양정보 조회"""
    url = "http://apis.data.go.kr/B552555/APTLttotPblancDetail/getLttotPblancSbjct"
    params = {
        "serviceKey": PUBLIC_DATA_API_KEY,
        "pageNo": 1,
        "numOfRows": 5,
        "dataType": "JSON"
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        if isinstance(items, dict):
            items = [items]
        return items
    except Exception as e:
        print(f"[청약 오류]: {e}")
        return []


def build_trade_message(all_trades):
    today = datetime.now().strftime("%m월 %d일 (%a)")
    weekday_map = {
        "Mon": "월", "Tue": "화", "Wed": "수",
        "Thu": "목", "Fri": "금", "Sat": "토", "Sun": "일"
    }
    for en, ko in weekday_map.items():
        today = today.replace(en, ko)

    lines = [f"[서울 아파트 실거래] {today}", ""]

    for district, trades in all_trades.items():
        if not trades:
            continue
        lines.append(f"▪ {district}")
        for t in trades[:3]:
            name = t.get("aptNm", "")
            area = t.get("excluUseAr", "")
            price = t.get("dealAmount", "").replace(",", "")
            floor = t.get("floor", "")
            try:
                price_str = f"{int(price.replace(' ', '')):,}만원"
            except:
                price_str = price + "만원"
            lines.append(f"  · {name} {area}㎡ {floor}층 → {price_str}")
        lines.append("")

    lines.append("─────────────────")
    lines.append("국토교통부 실거래가 기준")
    return "\n".join(lines)


def build_subscription_message(items):
    lines = ["[청약 정보]", ""]
    if not items:
        lines.append("현재 청약 공고가 없습니다.")
    else:
        for item in items[:5]:
            name = item.get("houseNm", "")
            region = item.get("subscrptAreaCode", "")
            start = item.get("rceptBgnde", "")
            end = item.get("rceptEndde", "")
            lines.append(f"  · {name}")
            lines.append(f"    지역: {region} | 접수: {start} ~ {end}")
            lines.append("")
    lines.append("─────────────────")
    lines.append("청약홈 기준")
    return "\n".join(lines)


def send_to_telegram(message, bot_token, chat_id):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            print("텔레그램 전송 성공!")
            return True
        else:
            print(f"텔레그램 전송 실패: {res.status_code} {res.text}")
            return False
    except Exception as e:
        print(f"텔레그램 전송 오류: {e}")
        return False


def main():
    yyyymm = datetime.now().strftime("%Y%m")

    print("아파트 실거래가 수집 시작...")
    all_trades = {}
    for district, code in SEOUL_DISTRICTS.items():
        trades = get_apt_trades(code, yyyymm)
        if trades:
            all_trades[district] = trades

    trade_msg = build_trade_message(all_trades)
    print(trade_msg)
    send_to_telegram(trade_msg, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)

    print("청약 정보 수집 시작...")
    sub_items = get_subscription_info()
    sub_msg = build_subscription_message(sub_items)
    print(sub_msg)
    send_to_telegram(sub_msg, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)


if __name__ == "__main__":
    main()
