import asyncio
import re
from playwright.async_api import async_playwright

def get_emoji(percentage_str):
    try:
        val = float(percentage_str.replace('%', ''))
        # Mapping logic:
        # Low score/ratio (clean) -> High score/ratio (bad/bot)
        # 0 - 10: ⚪ (White)
        # 10 - 30: 🟢 (Green)
        # 30 - 50: 🟡 (Yellow)
        # 50 - 70: 🟠 (Orange)
        # 70 - 90: 🔴 (Red)
        # 90+: ⚫ (Black)
        if val <= 10: return "⚪"
        if val <= 30: return "🟢"
        if val <= 50: return "🟡"
        if val <= 70: return "🟠"
        if val <= 90: return "🔴"
        return "⚫"
    except:
        return "❓"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # Navigate
            await page.goto("https://ippure.com/", wait_until="domcontentloaded", timeout=60000)
            
            # Wait for key specific text to ensure dynamic content loads
            # Waiting for "IPPure系数" or "人机流量比"
            try:
                await page.wait_for_selector("text=人机流量比", timeout=20000)
            except:
                print("Error: Page load timeout or bot challenge.")
                return

            # visual wait for values to populate
            await page.wait_for_timeout(2000) 

            # Extract full text for regex processing
            text = await page.inner_text("body")
            
            # 1. IPPure Score (IPPure系数)
            # Pattern looking for "IPPure系数" followed by number%
            score_match = re.search(r"IPPure系数.*?(\d+%)", text, re.DOTALL)
            pure_score = score_match.group(1) if score_match else "❓"
            pure_emoji = get_emoji(pure_score)

            # 2. Human/Bot Ratio (人机流量比)
            # Pattern looking for "bot" followed by percentage
            bot_match = re.search(r"bot\s*(\d+(\.\d+)?)%", text, re.IGNORECASE)
            bot_val = bot_match.group(0).replace('bot', '').strip() if bot_match else "❓"
            # Ensure we have the % sign
            if bot_val != "❓" and not bot_val.endswith('%'):
                 bot_val += "%"
            bot_emoji = get_emoji(bot_val)

            # 3. IP Attributes (IP属性)
            # Find "IP属性" line
            attr_match = re.search(r"IP属性\s*\n\s*(.+)", text) # Assuming newline after label
            if not attr_match:
                 attr_match = re.search(r"IP属性\s*(.+)", text)
            
            ip_attr = "❓"
            if attr_match:
                raw_attr = attr_match.group(1).strip()
                # Remove trailing "IP" if present (e.g. "机房IP" -> "机房")
                ip_attr = re.sub(r"IP$", "", raw_attr)

            # 4. IP Source (IP来源)
            # Find "IP来源" line
            src_match = re.search(r"IP来源\s*\n\s*(.+)", text)
            if not src_match:
                 src_match = re.search(r"IP来源\s*(.+)", text)
            
            ip_src = "❓"
            if src_match:
                raw_src = src_match.group(1).strip()
                ip_src = re.sub(r"IP$", "", raw_src)
            
            # Final Output Format: 【IPPure系数 人机流量比 IP属性 IP来源】
            # Example: 【⚪🟡 机房 广播】
            print(f"【{pure_emoji}{bot_emoji} {ip_attr} {ip_src}】")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
