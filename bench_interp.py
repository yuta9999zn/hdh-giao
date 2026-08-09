# -*- coding: utf-8 -*-
"""Đo + profile trình thông dịch GIAO (đường full-language) — fib đệ quy nặng."""
import time, sys, cProfile, pstats, io
sys.setrecursionlimit(40000)
from giao import tokenize, Parser, Runtime

SRC = "hàm fib(n){ nếu n<2 {trả n} trả fib(n-1)+fib(n-2) }\nđặt __ = fib(25)"

def chạy():
    rt = Runtime(); rt.MAX_STEPS = 10**9
    rt.exec_block(Parser(tokenize(SRC)).parse())
    return rt.glob["__"]

t = time.perf_counter(); kq = chạy(); dt = time.perf_counter() - t
print(f"THỜI GIAN: {dt:.3f}s   (fib(25)={kq})")

if "--prof" in sys.argv:
    ast = Parser(tokenize(SRC)).parse()
    rt = Runtime(); rt.MAX_STEPS = 10**9
    pr = cProfile.Profile(); pr.enable(); rt.exec_block(ast); pr.disable()
    st = pstats.Stats(pr); st.sort_stats("tottime")
    s = io.StringIO(); st.stream = s; st.print_stats(8); print(s.getvalue())
