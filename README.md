# 환경 설정

```
uv sync --extra build

```

# env API 키 발급

- https://www.tavily.com/
- https://arize.com/phoenix/
- https://langfuse.com/

# 학습 보충사이트

- https://poloclub.github.io/transformer-explainer/
    - 트랜스포머(Transformer) 모델이 어떻게 작동하는지 시각적으로 보여주고 설명해 주는 교육용 웹사이트

---

# 학습개념

- Context window
    - 인공지능 모델이 한번에 처리하고 기억할 수 있는 텍스트 데이터의 최대범위

- 생성 파라미터
    - Top-K와 Top-T(보통 온도인 Temperature T 또는 Top-P를 의미)는 인공지능이 다음 글자나 단어를 고를 때 후보 범위를 조절하는 핵심 매개변수

- 파인 튜닝(Fine-tuning, 미세 조정)
    - 이미 대규모 데이터로 사전 학습된 인공지능 모델을 특정 도메인이나 목적에 맞게 추가 학습시켜 최적화하는 과정