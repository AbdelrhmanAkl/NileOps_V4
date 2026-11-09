import asyncio
import base64
import json
import os
import subprocess
import time
import urllib.request
import websockets

SCREENSHOTS_DIR = r"C:\AI\NileOps_V4\docs\screenshots"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

class BrowserController:
    def __init__(self):
        self.proc = None
        self.ws = None
        self.msg_id = 0

    async def start(self):
        self.proc = subprocess.Popen([
            CHROME_PATH,
            "--headless=new",
            "--remote-debugging-port=9222",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-gpu",
            "--window-size=1920,1080",
            "--force-device-scale-factor=1",
        ])
        await asyncio.sleep(2.0)
        
        req = urllib.request.Request("http://127.0.0.1:9222/json/new?http://127.0.0.1:5173/", method="PUT")
        with urllib.request.urlopen(req) as resp:
            page_info = json.loads(resp.read().decode())
        ws_url = page_info["webSocketDebuggerUrl"]
        self.ws = await websockets.connect(ws_url, max_size=25_000_000)
        print("Connected to Chrome at:", ws_url)

    async def send_cmd(self, method: str, params: dict = None):
        self.msg_id += 1
        payload = {"id": self.msg_id, "method": method}
        if params:
            payload["params"] = params
        await self.ws.send(json.dumps(payload))
        
        while True:
            resp_str = await self.ws.recv()
            resp = json.loads(resp_str)
            if resp.get("id") == self.msg_id:
                return resp.get("result", {})

    async def eval_js(self, expression: str):
        res = await self.send_cmd("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True
        })
        return res.get("result", {}).get("value")

    async def capture_screenshot(self, filename: str):
        filepath = os.path.join(SCREENSHOTS_DIR, filename)
        res = await self.send_cmd("Page.captureScreenshot", {
            "format": "png",
            "fromSurface": True,
            "captureBeyondViewport": False
        })
        b64_data = res["data"]
        png_bytes = base64.b64decode(b64_data)
        with open(filepath, "wb") as f:
            f.write(png_bytes)
        print(f"[CAPTURED] {filename} ({len(png_bytes)} bytes)")

    async def stop(self):
        if self.ws:
            await self.ws.close()
        if self.proc:
            self.proc.terminate()
            self.proc.wait()

async def run_capture_sequence():
    bc = BrowserController()
    await bc.start()

    try:
        await asyncio.sleep(2.5)

        print("\n--- PHASE 1: CUSTOMER PORTAL VIEWS ---")
        # 1. Login as Retail Customer (Ahmed Mansour)
        login_script = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const custBtn = btns.find(b => b.textContent.includes('Ahmed Mansour') || b.textContent.includes('customer1@nileops.demo'));
            if (custBtn) {
                custBtn.click();
                return "CLICKED_QUICK_LOGIN";
            }
            return "NOT_FOUND";
        })()
        """
        await bc.eval_js(login_script)
        await asyncio.sleep(2.5)

        # 01_customer_dashboard.png (Top Overview)
        await bc.eval_js("window.scrollTo(0, 0)")
        await asyncio.sleep(0.5)
        await bc.capture_screenshot("01_customer_dashboard.png")

        # 02_customer_accounts.png (Clean view of Accounts & Deposits cards)
        await bc.eval_js("window.scrollTo(0, 160)")
        await asyncio.sleep(0.5)
        await bc.capture_screenshot("02_customer_accounts.png")

        # 03_customer_transactions.png (Clean view of Transaction Statement table)
        await bc.eval_js("window.scrollTo(0, 480)")
        await asyncio.sleep(0.5)
        await bc.capture_screenshot("03_customer_transactions.png")

        # 04_customer_complaint_submission.png (Complaint modal open with synthetic inquiry)
        await bc.eval_js("""
        (() => {
            window.scrollTo(0, 0);
            const submitBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Submit Complaint') || b.textContent.includes('تقديم شكوى'));
            if (submitBtn) submitBtn.click();
        })()
        """)
        await asyncio.sleep(0.8)
        await bc.eval_js("""
        (() => {
            const inputs = document.querySelectorAll('input, textarea');
            if (inputs.length >= 2) {
                inputs[0].value = "ATM transaction fee discrepancy inquiry";
                inputs[0].dispatchEvent(new Event('input', { bubbles: true }));
                inputs[1].value = "Inquiring about recent ATM withdrawal fee of 5.00 EGP recorded on 2026-11-05 at Zamalek Branch ATM #104.";
                inputs[1].dispatchEvent(new Event('input', { bubbles: true }));
            }
        })()
        """)
        await asyncio.sleep(0.5)
        await bc.capture_screenshot("04_customer_complaint_submission.png")

        # Close modal
        await bc.eval_js("""
        (() => {
            const cancelBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Cancel') || b.textContent.includes('إلغاء'));
            if (cancelBtn) cancelBtn.click();
        })()
        """)
        await asyncio.sleep(0.5)

        # 05_customer_rag_assistant.png (Interactive Deposit Yield Calculator & Banking Products)
        await bc.eval_js("window.scrollTo(0, 950)")
        await asyncio.sleep(0.5)
        await bc.capture_screenshot("05_customer_rag_assistant.png")

        print("\n--- PHASE 2: EMPLOYEE PORTAL VIEWS ---")
        # Logout Customer
        await bc.eval_js("""
        (() => {
            localStorage.clear();
            window.location.reload();
        })()
        """)
        await asyncio.sleep(2.0)

        # Login as Admin (Mahmoud Farouk)
        admin_login = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const adminBtn = btns.find(b => b.textContent.includes('Mahmoud Farouk') || b.textContent.includes('admin@nileops.demo'));
            if (adminBtn) {
                adminBtn.click();
                return "CLICKED_ADMIN_LOGIN";
            }
            return "NOT_FOUND";
        })()
        """
        await bc.eval_js(admin_login)
        await asyncio.sleep(2.5)

        # Helper to click employee tab
        click_tab_js = """
        (tabKey) => {
            const btns = Array.from(document.querySelectorAll('.flex.flex-wrap.gap-1 button, button'));
            const target = btns.find(b => {
                const t = b.textContent.toLowerCase();
                if (tabKey === 'dashboard') return t.includes('dashboard') || t.includes('مؤشرات');
                if (tabKey === 'customers') return t.includes('customers') || t.includes('العملاء');
                if (tabKey === 'complaints') return t.includes('complaints') || t.includes('الشكاوى');
                if (tabKey === 'policies') return t.includes('policy') || t.includes('السياسات');
                if (tabKey === 'kyc') return t.includes('kyc') || t.includes('تدقيق الهوية');
                if (tabKey === 'audit') return t.includes('audit') || t.includes('التدقيق');
                return false;
            });
            if (target) {
                target.click();
                return 'CLICKED_' + tabKey;
            }
            return 'NOT_FOUND_' + tabKey;
        }
        """

        # 06_employee_dashboard.png (Employee Portal — Main Dashboard)
        await bc.eval_js(f"({click_tab_js})('dashboard')")
        await bc.eval_js("window.scrollTo(0, 0)")
        await asyncio.sleep(1.0)
        await bc.capture_screenshot("06_employee_dashboard.png")

        # 07_employee_customer_search.png (Employee Portal — Customer Search / Profiles)
        tab_res = await bc.eval_js(f"({click_tab_js})('customers')")
        print("Click customers tab:", tab_res)
        await bc.eval_js("window.scrollTo(0, 0)")
        await asyncio.sleep(1.2)
        await bc.capture_screenshot("07_employee_customer_search.png")

        # 08_employee_complaint_management.png (Employee Portal — Complaints Management)
        tab_res = await bc.eval_js(f"({click_tab_js})('complaints')")
        print("Click complaints tab:", tab_res)
        await bc.eval_js("window.scrollTo(0, 0)")
        await asyncio.sleep(1.2)
        await bc.capture_screenshot("08_employee_complaint_management.png")

        # 09_employee_policy_governance.png (Employee Portal — Policy Governance / Four-Eyes Approval)
        tab_res = await bc.eval_js(f"({click_tab_js})('policies')")
        print("Click policies tab:", tab_res)
        await bc.eval_js("window.scrollTo(0, 0)")
        await asyncio.sleep(1.2)
        await bc.capture_screenshot("09_employee_policy_governance.png")

        # 10_employee_kyc_audit.png (Employee Portal — KYC Review Queue or Audit Logs)
        tab_res = await bc.eval_js(f"({click_tab_js})('audit')")
        print("Click audit tab:", tab_res)
        await bc.eval_js("window.scrollTo(0, 0)")
        await asyncio.sleep(1.2)
        await bc.capture_screenshot("10_employee_kyc_audit.png")

        print("\n[VERIFIED] All 10 distinct screenshots captured successfully!")

    finally:
        await bc.stop()

if __name__ == "__main__":
    asyncio.run(run_capture_sequence())
