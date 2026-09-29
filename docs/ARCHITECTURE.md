# 아키텍처

## 실행 구조

`app.py`가 Streamlit 설정과 내비게이션을 구성하고 `pages/`의 화면을 실행한다. 화면 계층은 사용자 입력과 세션 상태를 관리하며, 영상·탐지·판정·저장은 `core/` 모듈을 호출한다. 공통 경로, 탐지 대상, 임계값과 클립 설정은 `config.py`에 있다.

## 주요 구성 요소

- `app.py`: 애플리케이션 진입점, 공통 레이아웃과 페이지 등록
- `pages/0_대시보드.py`: 제품 설명과 저장 현황
- `pages/1_모니터링.py`: 로컬/RTSP 입력, 비동기 탐지, 위험 경고, 이벤트 녹화의 주 흐름
- `pages/2_ROI_설정.py`: 첫 프레임 위 다각형 ROI 편집과 소스별 JSON 저장
- `pages/3_이벤트_다시보기.py`: 이벤트 달력, 이미지·클립 재생 및 삭제
- `pages/4_성능_평가.py`: 평가 사례 입력과 탐지 지표 표시
- `core/video_source.py`: OpenCV 기반 로컬 영상·RTSP 읽기와 재연결
- `core/detector.py`: YOLOv8 객체 탐지 결과를 공통 딕셔너리 형식으로 변환. 추론 백엔드는 `config.INFER_BACKEND`로 고르며, OpenVINO로 내보낸 모델이 있으면 그것을, 없으면 기존 `yolov8n.pt`를 쓴다(반환 형식은 동일)
- `core/parked_detector.py`: 차량 추적 ID(ByteTrack)로 같은 차를 이어가며, 중심점 이동량·박스 크기 변화와 지속 시간으로 정지 차량 판정 (ID가 없으면 거리 기반 매칭으로 폴백)
- `core/image_enhancement.py`: 밝기 측정과 CLAHE 저조도 보정
- `core/roi_manager.py`: ROI JSON 영속화, 점 포함 판정, 프레임 표시
- `core/danger_logic.py`: 사람의 `bottom_center`와 이동 차량 존재 여부를 이용한 위험 판정 및 표시
- `core/event_saver.py`: 이벤트 이미지·클립·CSV 로그 관리
- `core/rtsp_presets.py`: `rtsp_presets.json` 카메라 프리셋 관리
- `core/performance_eval.py`: 평가 CSV와 Recall, Precision, FAR, Miss 계산

## 주요 데이터 흐름

영상 소스 → 저조도 보정 → 비동기 YOLO 탐지 → 정지 차량 표시 → ROI 위험 판정 → 화면/음향 경고 → 이미지·클립·CSV 저장 → 이벤트 다시보기 및 성능 평가

## 런타임 데이터

- `data/`: 업로드·샘플 영상
- `roi_configs/`: 소스별 ROI JSON
- `saved_events/`: 이벤트 이미지·클립과 변환본
- `logs/events_log.csv`: 이벤트 기록
- `logs/performance_eval.csv`: 수동 성능 평가 기록

이 디렉터리들은 실행 중 생성·변경될 수 있으므로 코드 변경과 구분한다.
