# TMLR 제출 패킷

작성 2026-08-31. 사전 검증은 전부 통과한 상태이며, 남은 것은 폼 입력과 업로드뿐이다.

## 사전 검증 결과 (2026-08-31 `make paper`)

| 항목 | 결과 |
|---|---|
| 빌드 | exit 0. tectonic 컴파일 통과 (경고는 Underfull \vbox 3건, 조판 여백) |
| 수치 정합 | `numbers.tex` 340 macros 재생성, **7/29 커밋본과 diff 0** |
| 재현성 | 재빌드한 PDF가 커밋본과 **바이트 동일** |
| 익명성 | `check_anonymity.py` 통과 — 6 identifying strings absent, 2 required markers present |
| 길이 | 총 12p. 본문은 `\section{Conclusion}`(748행) 뒤 `\bibliography`(796행)에서 종료 → **본문 12p 미만** ✅ |
| LLM 고지 | `\maketitle`(64) → `\footnotetext[1]`(67) → `\begin{abstract}`(72) → **1페이지 조판 확정** ✅ |
| 프리앰블 | `\usepackage{tmlr}` submission 모드. `[accepted]`/`[preprint]` 미적용 ✅ |
| OpenReview 프로필 | `~YoungminKo1` **활성 확인** (RL 논문 2026-08-31 제출로 검증) |

## Title (한 줄. 소스의 `\\` 제거)

```
How Much Do Time-Series Anomaly Detection Metrics Actually Disagree? Null Models and Cluster-Aware Inference for Rank-Flip Statistics
```

## Abstract

⚠️ **빌드 PDF에서 복사하지 말 것.** 줄번호·행분리 하이픈·fi/fl 합자가 섞인다.
아래는 `paper/numbers.tex`의 매크로 340개를 소스에서 직접 치환해 뽑은 것이다 (미해결 매크로 0).

```
Reports that point-level and segment-level metrics rank time-series anomaly detectors differently have become a standard argument for evaluation reform. These reports take the form of a rank-flip rate: the fraction of model pairs that two metrics order differently. We audit that statistic on a 180-series, 25-model recomputation of TSB-AD-M spanning 17 source collections, and on a 6-dataset, seven-detector grid. Our main finding is that evaluation series are treated as independent when they are not, and that this invalidates the standard alpha-based structural explanation built on top of the statistic. The covariate most often invoked to explain disagreement, the short-anomaly ratio alpha, is constant within 11 of the 12 collections that contain more than one series: it is a collection label rather than a series-level variable. Its rank correlation with the flip rate falls from 0.3241 at the series level to 0.0563 (p = 0.827) with collections as the unit, and to 0.0898 when one collection is removed. Interval estimates move the same way, from [0.2979, 0.3312] resampling series to [0.2695, 0.3715] clustering over collections; on the six-dataset grid the clustered interval spans [0.0667, 0.4167], which cannot resolve its magnitude. Two further omissions point the same way. Raw flip percentages are reported without stating the chance level, which is 0.5 and not 0: our observed 0.3145 against a permutation null of 0.5002 means the metrics agree on 68.6% of pairs. And flips are pooled across margins: among the 13.3% of pairs that both metrics separate by at least 0.20, a fraction of 0.0220 are ordered differently, so confident disagreement is roughly two percent rather than the 0.3145 that gets reported. We apply the audit to a composite metric we previously proposed ourselves and show it is uninformative by construction at both ends of the regime it was built to span. Applying the same corrections to our own positive findings leaves one covariate standing, segment count, at -0.6225 (p = 0.008) with collections as the unit. We give a reporting protocol and release code that regenerates every number here from committed artifacts.
```

## 필수 폼 필드

| 필드 | 값 |
|---|---|
| `competing_interests` | None. The author declares no competing interests. |
| `human_subjects_reporting` | N/A. This work is a re-analysis of public benchmark datasets (TSB-AD-M and TAB) and involves no human subjects. |

⚠️ **폼에 문서화되지 않은 필수 필드가 있을 수 있다.** 자매 프로젝트(RL)가 실제 제출에서 확인: OpenReview 폼에 **License 칸**(CC BY 4.0 단일 선택지, 필수)이 있는데 API 스펙에는 없었다. **제출 직전 폼 전체를 한 번 훑을 것.**

## 실행 순서

1. **제출** — 위 재료로 폼 작성 후 `paper/main.pdf` 업로드
   - 제출본에 **이 저장소를 링크하지 말 것** (저장소가 공개이고 저자 실명이 달려 있음)
   - Supplementary material은 선택. 넣는다면 git history·파일 메타데이터까지 익명화 필요
2. **제출 완료 후** 이 파일에 제출 기록(일시·submission ID·PDF 해시)을 남기고 커밋
3. **그다음** 로컬 12커밋 푸시 — `git pull --rebase origin main && git push origin main`
   - 순서 이유: 지금 푸시하면 이중맹검 심사 중 원고가 실명 저장소에 노출된다. TMLR이 preprint를 허용하므로 규정 위반은 아니지만, 제출 뒤로 미루면 비용 0으로 그 노출 창이 사라진다
4. **arXiv는 그 뒤** — `\usepackage[preprint]{tmlr}`로 전환하면 탈익명 버전이 나온다.
   단 **endorsement가 선행 조건**: 2026-01-21 정책 변경으로 기관 이메일만으로는 first-time submitter 자동 endorsement가 안 된다. cs.LG 등 해당 domain의 기존 arXiv 저자에게 개인 endorsement를 받아야 한다.
   arXiv에서 제출을 시작하면 필요한 endorsement code와 domain을 시스템이 알려주므로, **그 화면을 먼저 띄운 뒤** 부탁할 것

## 제출 기록

(제출 후 기입)

- 일시:
- Submission ID / URL:
- 업로드 PDF:
