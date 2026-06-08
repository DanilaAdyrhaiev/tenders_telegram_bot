import json
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def export_db_to_excel(json_path: str, excel_path: str) -> bool:
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # 1. Экспорт пользователей
            users_data = data.get('users', {})
            if users_data:
                df_users = pd.DataFrame(list(users_data.values()))
                df_users.to_excel(writer, sheet_name='Users', index=False)
            else:
                pd.DataFrame(columns=['telegram_id', 'nickname']).to_excel(writer, sheet_name='Users', index=False)

            # 2. Экспорт тендеров
            tenders_data = data.get('tenders', {})
            if tenders_data:
                tenders_list = list(tenders_data.values())
                # Конвертируем вложенные словари (предложения/победители) в строки, 
                # чтобы Excel корректно их отобразил
                for t in tenders_list:
                    if 'proposals' in t and isinstance(t['proposals'], list):
                        t['proposals'] = json.dumps(t['proposals'], ensure_ascii=False)
                    if 'winner' in t and isinstance(t['winner'], dict):
                        t['winner'] = json.dumps(t['winner'], ensure_ascii=False)
                
                df_tenders = pd.DataFrame(tenders_list)
                df_tenders.to_excel(writer, sheet_name='Tenders', index=False)
            else:
                pd.DataFrame(columns=['tender_id', 'text']).to_excel(writer, sheet_name='Tenders', index=False)
                
        return True
    except Exception as e:
        logger.error(f"Ошибка конвертации БД в Excel: {e}")
        return False