async def send_to_amocrm(user_id, name, phone, username, answers, rec):
    print("="*50)
    print(f"НОВАЯ ЗАЯВКА ОТ {name}")
    print(f"Телефон: {phone}")
    print(f"Telegram: @{username}")
    print(f"Рекомендации: {len(rec['procedures'])} процедур")
    print("="*50)
    
    with open("zayavki.txt", "a", encoding="utf-8") as f:
        f.write(f"{name} | {phone} | @{username}\n")
    
    return {"success": True}