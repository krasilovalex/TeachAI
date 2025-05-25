import requests

AUTH_KEY = "your auth key"  # В формате base64 от client_id:client_secret
TOKEN_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

def get_gigachat_access_token():
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": "6f450b63-ebd7-46d0-91cd-b0673b1a8c09",  # можешь сгенерировать UUID, но и этот подойдёт
        "Authorization": f"Basic {AUTH_KEY}"
    }

    data = {
        "scope": "GIGACHAT_API_PERS"
    }

    try:
        response = requests.post(TOKEN_URL, headers=headers, data=data, verify=False, timeout=60)
        response.raise_for_status()
        access_token = response.json().get("access_token")
        return access_token if access_token else "Токен не найден в ответе."
    except Exception as e:
        return f"Ошибка при получении токена: {e}"

# Пример вызова
if __name__ == "__main__":
    token = get_gigachat_access_token()
    print("Access Token:", token)
