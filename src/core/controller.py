from PySide6.QtCore import QObject, Signal
from typing import Any, Dict, Optional, Set, Callable
from natsort import natsorted
from pathlib import Path
# 自訂庫
from src.signal_bus import SIGNAL_BUS
from src.global_data_store import GLOBAL_DATA_STORE
from src.core.file_read_write import FileReadWrite
from src.core.data_process import DataProcess

class BackendCore(QObject):
    def __init__(self):
        super().__init__()
        # 資料集初始化
        langFileData = self.getLangFilesData()
        if len(langFileData) == 0: langFileData = {"無檔案": ""}
        GLOBAL_DATA_STORE.update({
            "source_dir": "",
            "output_dir": "",
            "output_ext": "cbz",
            "file_list": [],
            "file_metadata_cache": {},
            "write_mode": 0,
            "font_size": 10,
            "image_exts": [
                ".jpg",
                ".jpeg",
                ".png",
                ".webp",
                ".bmp",
                ".gif",
            ],
            "allow_files": [
                ".nomedia",
            ],
            "langFileData": langFileData,
            "selectedLang": "zh_TW" if ("zh_TW" in langFileData.keys()) else langFileData.keys()[0],
        })

        # 後端實例化
        self.file_read_write = FileReadWrite()
        self.data_process = DataProcess()

        # 資料變更追蹤
        GLOBAL_DATA_STORE.subscribe(self.on_data_change)

        # 訊號連接
        self.signal_connection()

    ### 初始化函式 ###

    def signal_connection(self) -> None:
        """ 訊號連接 """
        # 漫畫檔案讀取完成
        SIGNAL_BUS.fileReadReady.connect(self.on_file_read_ready)
        # 漫畫列表排序
        SIGNAL_BUS.comicListSort.connect(self.comic_list_sort)

    ### 功能函式

    def on_data_change(self, change: Dict[str, Any]) -> None:
        """ 資料變更處理 """
        keys = change.keys()
        if len(keys) == 0 :
            return
        # 字體改變
        if "font_size" in keys:
            SIGNAL_BUS.appSetting.fontSizeChanged.emit(GLOBAL_DATA_STORE.get("font_size"))
        # 寫入模式改變
        if "write_mode" in keys:
            SIGNAL_BUS.appSetting.writeModeChanged.emit(GLOBAL_DATA_STORE.get("write_mode"))
        # 漫畫資料夾變更
        if "source_dir" in keys:
            SIGNAL_BUS.dataChange.sourceDirChanged.emit(GLOBAL_DATA_STORE.get("source_dir"))
        # 輸出資料夾變更
        if "output_dir" in keys:
            SIGNAL_BUS.dataChange.outputDirChanged.emit(GLOBAL_DATA_STORE.get("output_dir"))
        # 副檔名選擇改變
        if "output_ext" in keys:
            SIGNAL_BUS.dataChange.outputExtChanged.emit(GLOBAL_DATA_STORE.get("output_ext"))
        # 漫畫列表變更
        if "file_list" in keys:
            SIGNAL_BUS.dataChange.fileListChanged.emit(GLOBAL_DATA_STORE.get("file_list").copy())
        # 漫畫快取變更
        if "file_metadata_cache" in keys:
            SIGNAL_BUS.dataChange.fileMetadataCacheChanged.emit(GLOBAL_DATA_STORE.get("file_metadata_cache").copy())
        # 圖片附檔名變更
        if "image_exts" in keys:
            SIGNAL_BUS.appSetting.imageExtChanged.emit(GLOBAL_DATA_STORE.get("image_exts").copy())
        # 允許檔案變更
        if "allow_files" in keys:
            SIGNAL_BUS.appSetting.allowFilesChanged.emit(GLOBAL_DATA_STORE.get("allow_files").copy())
        # 語言變更
        if "selectedLang" in keys:
            SIGNAL_BUS.appSetting.langChanged.emit(GLOBAL_DATA_STORE.get("selectedLang")) # 傳遞檔案絕對路徑


    def on_file_read_ready(self) -> None:
        """ 漫畫檔案讀取完成 """
        # 更新選擇狀態提示
        SIGNAL_BUS.ui.selectionStatusChange.emit(0)

    def comic_list_sort(self, mode) -> None:
        """ 漫畫列表排序 """
        # 不知道怎麼分類比較好，先寫在這
        file_list = GLOBAL_DATA_STORE.get("file_list").copy()

        if mode == 0:
            pass
        elif mode == 1:
            file_list = natsorted(file_list)
        elif mode == 2:
            file_metadata_cache = GLOBAL_DATA_STORE.get("file_metadata_cache")
            file_list = sorted(
                            file_list,
                            key=lambda x: int(
                                file_metadata_cache
                                    .get(x, {})
                                    .get("_fields", {})
                                    .get("base", {})
                                    .get("Number", len(file_list) + 1)
                                )
                        )
        else:
            return
        # 刷新
        GLOBAL_DATA_STORE.update({
            "file_list": file_list
        })
        # 刷新選擇欄顯示
        SIGNAL_BUS.ui.comicListSortDisplayChange.emit(mode)

    def getLangFilesData(self, path:str = "translations"):
        """ 取得擁有的 .qm 翻譯檔案 """
        folder = Path(path).resolve()
        return { file.name.replace(".qm", ""): str(file.resolve()) for file in folder.glob("*.qm")}

    

