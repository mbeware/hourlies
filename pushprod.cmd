@echo off
copy hourlies.py C:\Users\mbelanger\AppData\Local\hourlies\hourlies.pyw
IF EXIST "C:\Users\mbelanger\AppData\Local\linkbin\hourlies.pyw" (
    del C:\Users\mbelanger\AppData\Local\linkbin\hourlies.pyw
)
mklink C:\Users\mbelanger\AppData\Local\linkbin\hourlies.pyw C:\Users\mbelanger\AppData\Local\hourlies\hourlies.pyw
