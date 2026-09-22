# 악천후 검증(GTA V 시뮬레이션 / 날씨 합성) 참고 자료

교수님 피드백으로 나온 "GTA V 인게임 날씨로 시스템을 예비 검증해보자"는 제안과 관련해, 학계에 실제로 어떤 선례·방법론이 있는지 찾아 정리한 자료입니다. 팀 내부 논의용 참고 자료이며, 최종 채택 여부는 팀 회의에서 결정합니다.

## 요약 결론

- **GTA V 기반 예비 검증은 학계에 실제 선례가 있는 정당한 방법론**입니다. 다만 "실제 4계절 테스트의 대체"가 아니라 **"실제 테스트가 불가능한 상황에서의 예비/보조 검증"**으로 정직하게 포지셔닝하는 걸 권장합니다.
- 대안으로 검토한 **물리 기반 날씨 합성(비/안개 오버레이)**은 실제 카메라로 찍은 진짜 영상에 날씨 효과만 얹는 방식이라, GTA V의 근본적 약점(게임 렌더링이라 생기는 sim-to-real gap)이 더 작습니다. OpenCV로 직접 구현 가능한 수준이라 GTA V보다 오히려 안전한 선택일 수 있습니다.
- **범용 생성형 AI 영상 툴(런웨이류)로 날씨를 바꾸는 방식은 비권장**입니다 — 픽셀 색 분포만 바뀌고 실제 날씨 질감은 재현 안 되는 한계, 탐지 실패 원인이 날씨 때문인지 툴 아티팩트 때문인지 구분 안 되는 문제가 문서화돼 있습니다.

## GTA V 기반 합성 데이터 (원조 ~ 최신)

| 자료 | 저자·출처 (연도) | 핵심 내용 |
|---|---|---|
| [Playing for Data: Ground Truth from Computer Games](https://arxiv.org/abs/1608.02192) | Richter et al., ECCV 2016 | GTA V 렌더링 명령어를 가로채 시맨틱 세그멘테이션 정답 데이터 25,000장을 자동 생성한 원조 논문. [코드(GitHub)](https://github.com/visinf/playing-for-data) |
| [Playing for Benchmarks](https://arxiv.org/pdf/1709.07322) | Richter et al., ICCV 2017 | GTA V 기반 25만+ 프레임 규모로 확장, 2D 객체 탐지·추적까지 포함한 벤치마크(VIPER). [프로젝트 페이지](https://playing-for-benchmarks.org/) |
| [PreSIL Dataset](https://arxiv.org/abs/1905.00160) | Hurl et al., Univ. of Waterloo | GTA V 기반, 주/야간·흐림 등 날씨 조건별 이미지에 사람·차량 바운딩박스가 달린 자율주행 인지용 데이터셋(5만+ 인스턴스). 방향성이 우리 프로젝트와 거의 동일. |
| [From Gaming to Research: GTA V for Synthetic Data Generation for Robotics and Navigations](https://arxiv.org/abs/2502.12303) | Scucchia, Ferrara, Maltoni, 2025 | 2025년 최신 논문 — GTA V 기반 합성 데이터가 지금도 계속 쓰이는 방법론임을 보여줌 (SLAM/VPR 분야). |

## 악천후 조건 벤치마크

| 자료 | 저자·출처 (연도) | 핵심 내용 |
|---|---|---|
| [DAWN: Vehicle Detection in Adverse Weather Nature Dataset](https://arxiv.org/abs/2008.05402) | Kenk & Hassaballah | 실제 도로 이미지 1,000장을 안개·비·눈·모래폭풍 4개 조건으로 나눈 벤치마크. "날씨별로 탐지 성능이 달라지는지"가 이 분야에서 인정받는 정당한 평가축임을 보여줌. [Kaggle 데이터셋](https://www.kaggle.com/datasets/shuvoalok/dawn-dataset) |

## 물리 기반 날씨 합성 (실제 영상 + 날씨 효과만 렌더링)

| 자료 | 저자·출처 (연도) | 핵심 내용 |
|---|---|---|
| [Semantic Foggy Scene Understanding with Synthetic Data (Foggy Cityscapes)](https://arxiv.org/abs/1708.07819) | Sakaridis, Dai, Van Gool, IJCV 2018 | 깊이 정보를 이용해 실제 사진(Cityscapes)에 안개를 물리적으로 렌더링. [프로젝트 페이지](https://people.ee.ethz.ch/~csakarid/SFSU_synthetic/) |
| [Rain Rendering for Evaluating and Improving Robustness to Bad Weather](https://arxiv.org/abs/2009.03683) | Tremblay et al., IJCV | 실제 KITTI/Cityscapes 영상에 빗줄기를 물리 기반으로 합성. **비 오는 조건에서 객체 탐지 성능 약 15% 하락, 이 합성 데이터로 파인튜닝 시 21% 개선을 실측 확인**. [코드(GitHub)](https://github.com/astra-vision/rain-rendering) |

## Sim-to-real gap (한계를 다루는 최근 연구)

| 자료 | 저자·출처 (연도) | 핵심 내용 |
|---|---|---|
| [Diffusion Dataset Generation: Towards Closing the Sim2Real Gap for Pedestrian Detection](https://arxiv.org/abs/2305.09401) | Farley, Zand, Greenspan, 2023 | 시뮬레이션 데이터와 실제 데이터 사이의 도메인 차이(sim-to-real gap)를 다루는 최근 연구. GTA V/게임 렌더링 기반 검증의 알려진 한계를 학계가 어떻게 인지·보완하고 있는지 보여주는 참고 사례. |

## 우리 프로젝트에 적용한다면 (제안)

1. 날씨 조건을 5~6개로 체계적으로 정하기: 맑음 / 비 / 눈 / 안개 / 야간+비 / 야간+눈
2. 팀원 2명이 이미 성공한 예비 테스트를 발판 삼아, 각 조건별 짧은 클립 여러 개 녹화
3. 이미 만들어둔 `4_성능_평가.py` / `performance_eval.csv` 틀에 그대로 넣어서 날씨별 정탐·오탐률을 숫자로 비교 (성능평가 데이터 완결성 작업과 자연스럽게 합쳐짐)
4. 보고서엔 "GTA V 시뮬레이션 기반 예비 검증, sim-to-real gap 존재를 인지하고 있음"이라고 명시
