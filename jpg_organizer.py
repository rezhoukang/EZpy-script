#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JPG 文件整理工具
根据文件名中"接"字的匹配关系，将根目录下的 JPG 文件移动到对应的子文件夹中。
"""

import os
import re
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from datetime import datetime


def extract_base_name(filename):
    """从 'name (数字).JPG' 中提取 name 部分，循环去掉所有尾部 (数字) 和扩展名"""
    name, ext = os.path.splitext(filename)
    if ext.lower() not in ('.jpg', '.jpeg'):
        return None
    while True:
        new_name = re.sub(r'\s*[\(（]\d+[\)）]\s*$', '', name).strip()
        if new_name == name:
            break
        name = new_name
    return name or None


def scan_and_move(root_folder):
    """扫描并执行文件移动，返回 (报告内容, 报告文件路径)"""
    reports = []
    report_index = 0

    # ---- 第一步：收集根目录下的 JPG 文件，按 base_name 分组 ----
    root_b_files = {}
    for f in os.listdir(root_folder):
        if not os.path.isfile(os.path.join(root_folder, f)):
            continue
        b = extract_base_name(f)
        if b is not None:
            root_b_files.setdefault(b, []).append(f)

    if not root_b_files:
        return "此次报告：\n（根目录下未发现 JPG 文件）\nover\n", None

    # ---- 第二步：扫描子文件夹，寻找含 "接{b}" 模式的 JPG 文件 ----
    # b_value -> {folder_path: representative_filename}
    b_to_folders = {}
    # 按长度降序排列，优先匹配最长的 b 值，避免子串误匹配
    sorted_b_values = sorted(root_b_files.keys(), key=len, reverse=True)

    for item in os.listdir(root_folder):
        item_path = os.path.join(root_folder, item)
        if not os.path.isdir(item_path):
            continue
        for dirpath, _, filenames in os.walk(item_path):
            for f in filenames:
                base = extract_base_name(f)
                if base is None:
                    continue
                for b_value in sorted_b_values:
                    if base.endswith('接' + b_value):
                        b_to_folders.setdefault(b_value, {})
                        if dirpath not in b_to_folders[b_value]:
                            b_to_folders[b_value][dirpath] = f
                        break

    # ---- 第三步：执行匹配与移动 ----
    for b_value, files in root_b_files.items():
        report_index += 1
        count = len(files)
        file_label = f"{b_value}.JPG"

        if b_value not in b_to_folders:
            # 类型 3：未找到匹配文件夹
            reports.append(
                f"#{report_index}#  {file_label}（{count}张）未移动，"
                f"未检测到可供移动的文件夹"
            )
        else:
            folder_dict = b_to_folders[b_value]
            if len(folder_dict) > 1:
                # 类型 2：多个匹配文件夹
                parts = [
                    f"含有{mf}文件的{os.path.basename(fp)}文件夹"
                    for fp, mf in folder_dict.items()
                ]
                reports.append(
                    f"#{report_index}#  {file_label}（{count}张）未移动，"
                    f"检测到超过一个的文件夹可供移动，"
                    f"分别为{'和'.join(parts)}，请您自行移动"
                )
            else:
                # 类型 1：唯一匹配，执行移动
                target_folder = list(folder_dict.keys())[0]
                matched_file = list(folder_dict.values())[0]
                folder_name = os.path.basename(target_folder)
                for f in files:
                    src = os.path.join(root_folder, f)
                    dst = os.path.join(target_folder, f)
                    if os.path.exists(dst):
                        base, ext = os.path.splitext(f)
                        i = 1
                        while os.path.exists(dst):
                            dst = os.path.join(target_folder, f"{base}({i}){ext}")
                            i += 1
                    shutil.move(src, dst)
                reports.append(
                    f"#{report_index}#  将{file_label}（{count}张）移动到"
                    f"含有{matched_file}文件的文件夹{folder_name}中"
                )

    # ---- 生成报告文件 ----
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(root_folder, f"{timestamp}_执行报告.txt")

    lines = ["此次报告：\n"]
    for r in reports:
        lines.append(r + "\n")
        lines.append("################################################\n")
    lines.append("over\n")
    report_content = "".join(lines)

    with open(report_path, 'w', encoding='utf-8') as fout:
        fout.write(report_content)

    return report_content, report_path


# ======================== GUI ========================

class App:
    def __init__(self, master):
        master.title("JPG 文件整理工具")
        master.geometry("750x520")
        master.resizable(True, True)

        # ---- 顶部：文件夹选择 ----
        frm_top = tk.Frame(master, padx=10, pady=10)
        frm_top.pack(fill=tk.X)

        tk.Label(frm_top, text="目标文件夹：").pack(side=tk.LEFT)
        self.path_var = tk.StringVar()
        tk.Entry(frm_top, textvariable=self.path_var, width=55).pack(
            side=tk.LEFT, padx=5, fill=tk.X, expand=True
        )
        tk.Button(frm_top, text="浏览…", command=self._browse).pack(side=tk.LEFT)

        # ---- 中部：执行按钮 ----
        frm_btn = tk.Frame(master, padx=10, pady=5)
        frm_btn.pack(fill=tk.X)
        tk.Button(
            frm_btn, text="▶ 执行整理", command=self._execute,
            bg="#4CAF50", fg="white",
            font=("Microsoft YaHei", 11, "bold"),
            width=18, height=1,
        ).pack()

        # ---- 底部：报告展示 ----
        frm_log = tk.Frame(master, padx=10, pady=5)
        frm_log.pack(fill=tk.BOTH, expand=True)
        tk.Label(frm_log, text="执行报告：").pack(anchor=tk.W)
        self.log = scrolledtext.ScrolledText(
            frm_log, wrap=tk.WORD, font=("Consolas", 10)
        )
        self.log.pack(fill=tk.BOTH, expand=True)

    def _browse(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_var.set(folder)

    def _execute(self):
        folder = self.path_var.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("错误", "请先选择一个有效的文件夹路径")
            return

        try:
            content, report_path = scan_and_move(folder)
            self.log.delete("1.0", tk.END)
            self.log.insert(tk.END, content)
            if report_path:
                self.log.insert(tk.END, f"\n\n报告已保存至：{report_path}\n")
                messagebox.showinfo("完成", f"执行完成！\n报告已保存至：\n{report_path}")
            else:
                messagebox.showinfo("完成", "执行完成！根目录下未发现 JPG 文件。")
        except Exception as e:
            messagebox.showerror("执行出错", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
