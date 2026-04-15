
# VLLM for agrinet model

```bash
cd ~
source mhvenv/bin/activate
nohup env CUDA_VISIBLE_DEVICES=0,1,2,3 \
vllm serve kenpath/mahavistaar-llm-v1 \
  --served-model-name agrinet-model \
  --dtype bfloat16 \
  --tensor-parallel-size 4 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder \
  --reasoning-parser qwen3 \
  --enable-prefix-caching \
  --enable-chunked-prefill \
  --kv-cache-dtype fp8 \
  --gpu-memory-utilization 0.95 \
  --max-model-len 84000 \
  --max-num-seqs 128 \
  --language-model-only \
  --port 8080 \
  --trust-remote-code \
  > vllm_agrinet.log 2>&1 &
```

# VLLM for moderation 
```bash
cd ~
source modvenv/bin/activate
nohup env CUDA_VISIBLE_DEVICES=4,5 vllm serve openai/gpt-oss-safeguard-20b \
  --served-model-name moderation-model \
  --enable-auto-tool-choice \
  --tool-call-parser openai \
  --tensor-parallel-size 2 \
  --gpu-memory-utilization 0.95 \
  --max-model-len 4096 \
  --max-num-batched-tokens 4096 \
  --max-num-seqs 128 \
  --port 8081 \
  --enable-prefix-caching \
  --enable-chunked-prefill \
  --trust-remote-code > moderation-vllm.log 2>&1 &
```