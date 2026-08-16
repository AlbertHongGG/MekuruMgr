import uvicorn
from src.core.config import app_settings

if __name__ == "__main__":
    print(f"啟動 ComicMgr 伺服器於 {app_settings.host}:{app_settings.port} ...")
    
    # 啟動 Uvicorn 伺服器
    # 這裡我們開啟了 reload=True，方便您在開發階段修改程式碼時，伺服器會自動重啟
    uvicorn.run(
        "src.server.app:app",
        host=app_settings.host,
        port=app_settings.port,
        reload=True
    )
