FROM nvidia/cuda:12.1.1-devel-ubuntu22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN --mount=type=cache,target=/var/cache/apt apt-get update && apt-get install -y python3.11 curl git git-lfs
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11
WORKDIR /app
RUN git clone https://github.com/mlc-ai/mlc-llm
WORKDIR /app/mlc-llm
RUN git submodule init && git submodule update
RUN --mount=type=cache,target=/root/.cache/pip pip install . && pip install --pre -f https://mlc.ai/wheels mlc-chat-nightly-cu121 mlc-ai-nightly-cu121
ENV CUDA_ARCH_LIST="80;86;90" 
# you need to login here
CMD python3.11 -m mlc_llm.build --hf-path dist/models/Llama-2-70b-chat-hf --target 'cuda-multiarch' --quantization q4f16_1 --use-cuda-graph
# disable cutlass for sm90
# https://github.com/mlc-ai/mlc-llm/issues/790
# python3.11 -m mlc_llm.build --hf-path meta-llama/Llama-2-70b-chat-hf --target 'cuda-multiarch' --quantization q4f16_1 --use-cuda-graph --no-cutlass-attn --no-cutlass-norm

