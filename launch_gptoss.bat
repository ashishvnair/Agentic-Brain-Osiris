@echo off
REM ============================================================
REM gpt-oss-120b (F16 / MXFP4_MOE) via llama-server + CUDA
REM RTX 3060 12GB / Ryzen 7 5800X (8 physical cores, 16 threads) / 64GB RAM
REM
REM gpt-oss-120b: 36 layers, ~117B total / 5.1B active, experts natively
REM MXFP4. (Earlier draft of this file said block_count=43 - that's
REM DeepSeek V4 Flash's layer count, carried over by mistake when this
REM was adapted from the DeepSeek launcher.)
REM
REM WHY THE PREVIOUS VERSION CRASHED: it had -ngl 99 alongside -fit on.
REM That's the exact conflict diagnosed for DeepSeek - an explicit -ngl
REM makes fit abort its own placement calculation entirely ("n_gpu_layers
REM already set by user to 99, abort"). There, an explicit -ncmoe still
REM caught the fallback. Here there was no -ncmoe at all, so llama.cpp
REM tried to place every layer's experts - the full ~65GB model - onto a
REM 12GB card. Not a shared-memory overflow like before; a straight
REM allocation failure, ~5x over what the card has.
REM
REM FIX: manual -ncmoe instead of fighting -fit, same approach as the
REM DeepSeek setup once fit proved unreliable there.
REM
REM -ncmoe 32 is a REAL, community-measured starting point (same
REM technique, UD-Q4_K_XL quant, 15 tok/s reported) - expert size is
REM close to identical between that quant and this F16 one, since the
REM experts are natively MXFP4 either way; only the small non-expert
REM remainder differs between quant labels.
REM
REM Sweep from here via Task Manager, same method as DeepSeek: if it loads
REM with Dedicated GPU memory well under 12GB and Shared GPU memory at 0,
REM step down (31, 30, ...) for more on GPU. If Shared goes non-zero or it
REM OOMs, step back up.
REM ============================================================
D:\llm\llama.cpp\build\bin\Release\llama-server.exe ^
  -m D:\llm\models\gpt-oss-120b-GGUF\gpt-oss-120b-F16.gguf ^
  -nr -ncmoe 32 -fa on --jinja --no-warmup ^
  -c 16384 -t 16 -tb 16 -np 2 ^
  -b 4096 -ub 2048 ^
  --cache-type-k q8_0 --cache-type-v q8_0 ^
  --host 127.0.0.1 --port 8080
pause