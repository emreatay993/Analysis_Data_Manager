from typing import List

try:
    import win32com.client  # type: ignore
except Exception:  # pragma: no cover
    win32com = None  # type: ignore


def send_email(subject: str, body: str, to: List[str], cc: List[str] | None = None) -> bool:
    cc = cc or []
    if not to and not cc:
        return False
    if win32com is None:
        # Fallback for dev machines without Outlook
        print("[EMAIL SIMULATION]", subject)
        print("TO:", ", ".join(to))
        if cc:
            print("CC:", ", ".join(cc))
        print(body)
        return True
    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)
        mail.Subject = subject
        mail.Body = body
        mail.To = "; ".join([x for x in to if x])
        if cc:
            mail.CC = "; ".join([x for x in cc if x])
        mail.Send()
        return True
    except Exception as e:  # pragma: no cover
        print("Email send failed:", e)
        return False
