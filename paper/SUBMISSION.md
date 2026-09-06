# 제출 패킷 — TMLR #11830 데스크 리젝(9/6) → **DMLR 제출 완료(9/6)**, "DMLR 제출 기록" 절 참조

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
| **`make verify` 전체 게이트** | **통과 (exit 0)** — pytest → 아티팩트 재계산 → `git diff --exit-code -- experiments/results` → numbers 재생성 → `git diff --exit-code -- paper/numbers.tex` → 컴파일 → 익명성 → `git diff --exit-code -- paper/main.pdf`. 전부 재계산 후에도 커밋본과 **한 바이트도 다르지 않음** |

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
4. **arXiv는 그 뒤** — 아래 "arXiv 준비" 참조

## arXiv 준비 (제출·통보와 무관하게 미리 해둘 수 있음)

### TMLR 심사 중에 arXiv에 올려도 되는가 — 된다

TMLR author guide가 명시한다: *"Authors are also allowed to upload their submissions to arXiv or other preprint servers at any time, either anonymously or including their identity"* — **실명으로, 시점 제약 없이** 허용된다.

붙어 있는 조건은 하나뿐이다: *"double blind of the TMLR submission itself must be maintained by **not linking to another version that includes the authors' names**."*

즉 제약은 arXiv 쪽이 아니라 **TMLR 제출본 쪽**에 걸린다. 제출본 PDF가 실명 버전(arXiv·저장소)을 링크하면 안 된다. 현재 `check_anonymity.py`가 저장소 URL·프로젝트 페이지 호스트를 금지 문자열로 잡고 있어 이미 지켜지고 있고, arXiv 게시 후에도 **제출본에 arXiv 링크를 추가하지 말 것**. 이 파일이나 README에 링크를 적는 것은 무관하다 — 제약은 제출된 PDF에만 걸린다.

### 빌드는 끝나 있다 — `make arxiv`

`\email`이 비어 있던 문제(과거 🔴 블로커)는 해소됐다. `scripts/build_arxiv.py`가 소스를 복사해 두 곳을 고쳐 빌드한다:

- `\usepackage{tmlr}` → `\usepackage[preprint]{tmlr}` (tmlr.sty가 저자 블록을 드러내는 스위치)
- 비어 있는 `\email` → 실제 주소

```bash
make arxiv                                   # 기본 주소
make arxiv ARXIV_EMAIL=you@example.com       # 주소 교체
```

산출물은 `paper/arxiv/`(gitignore)에 떨어진다:

- `main.pdf` — 탈익명 프리프린트. 2026-08-31 빌드 기준 12p, 첫 장에 `Youngmin Ko ymk5292@psu.edu / Pennsylvania State University` 노출 확인
- `arxiv-submission.tar.gz` — **업로드는 이걸 쓴다.** arXiv는 PDF가 아니라 LaTeX 소스를 받는다. `main.bbl`을 포함시킨 이유: arXiv 공식 문서 기준 **`.bbl`이 있으면 그걸 쓰고, 없을 때만 자체 BibTeX를 돌린다** — 우리 빌드의 참고문헌을 그대로 고정하려는 것이다 (과거 문서의 "arXiv는 BibTeX를 안 돌린다"는 서술은 현재 정책과 달라 폐기). 내용물: `main.tex`, `main.bbl`, **`refs.bib`**, `tmlr.sty`, `tmlr.bst`, `fancyhdr.sty`, `numbers.tex`. **`refs.bib`를 빼면 안 된다** — 2026-08-31 실측: `.bib` 없는 패키지를 tectonic으로 빌드하자 BibTeX 재실행이 조용히 실패해 **참고문헌 전체가 사라지고(12p→10p) 인용이 `(?)`로 남았다.** 에러가 아니라 경고로만 나오므로 눈으로 안 보면 모른다. `.bbl`과 `.bib`가 어긋날 일은 없다(같은 `.bib`·`.bst`에서 생성). 업로드 전 **tarball만 풀어서 따로 컴파일해 12p·`(?)` 0개를 확인**할 것

**제출본은 건드리지 않는다.** `paper/main.pdf`는 TMLR에 올라간 그 파일이고 `make verify`가 바이트 단위로 고정하고 있으므로, 탈익명 빌드를 그 위에 덮으면 게이트가 깨진다. 그래서 별도 디렉토리다. `make arxiv` 실행 후에도 `git status`에 `paper/` 변경이 없어야 정상이다.

`check_anonymity.py --allow-identified`는 이제 **탈익명 빌드를 통과시키고, 오히려 아무도 식별되지 않으면 실패한다** — `[preprint]` 옵션이 안 먹은 채 잘못된 PDF를 올리는 걸 막는 방향으로 뒤집혀 있다. (예전 문서가 "의도적으로 실패한다"고 적었던 부분은 폐기.)

⚠️ **남은 기술 리스크 1건**: 로컬 빌드는 tectonic(XeTeX)이고 arXiv 공식 문서는 pdflatex/DVI 모드만 명시한다(XeLaTeX 언급 없음). 이 기계에 pdflatex가 없어 사전 검증은 못 했다. 완화 근거: `main.tex`에 비ASCII 문자 0개, 그림 파일 0개, 패키지는 전부 표준. `\pdfoutput=1`은 arXiv가 쓰지 말라고 명시하므로 넣지 않았다. 업로드 후 arXiv가 생성한 PDF를 **승인 전에 반드시 눈으로 확인**할 것. 어긋나면 PDF 직접 업로드로 우회할 수 있다.

**남은 결정 1건 — 인쇄될 이메일 주소**: 기본값 `ymk5292@psu.edu`는 2026-08 졸업한 학교 계정이다. arXiv 프리프린트는 영구 공개물이라 수년 뒤에도 닿는 주소여야 한다. 졸업생 계정 유지 정책을 확인하고, 끊긴다면 `make arxiv ARXIV_EMAIL=...`로 영구 주소를 넣을 것.

### arXiv 실측 상태 (2026-09-06)

- **계정 있음**: username `Youngmin05`, 계정 이메일 **`rhdudals0505@naver.com`**(Gmail·PSU 아님), 소속 PSU, 기본 카테고리 cs.LG. arXiv의 모든 메일(endorsement code, 처리 결과)은 **네이버로 간다**
- **제출 레코드 있음**: `submit/7545844` (incomplete, **2026-09-20 만료** — 그 전에 endorsement가 안 되면 새로 시작해야 함). 2026-09-06에 Start 단계 완료: 연락처 확인, Submittal Agreement 수락, 저자 본인, **CC BY 4.0**, primary **cs.LG**
- **endorsement 벽에서 정지**: "You are not endorsed for this archive." 파일 업로드·메타데이터는 endorsement 후에만 진행 가능
- **endorsement code 발급됨: `KQOI4O`** — 같은 코드가 네이버 메일로도 감. endorser에게 줄 링크: `https://arxiv.org/auth/endorse?x=KQOI4O` (네이버 메일의 링크가 정본)
- **endorser 자격(cs.LG, arXiv 명시)**: 최근 **3개월~5년 사이에 cs.* 아무 카테고리에 논문 3편 이상** 제출한 사람. 특정인이 자격이 있는지는 그 사람 논문 abstract 페이지 하단 "Which of the authors of this article can endorse?" 링크로 확인 가능

### arXiv 제출 순서

1. **endorsement가 유일한 블로커.** [arXiv 공지(2026-01-21)](https://blog.arxiv.org/2026/01/21/attention-authors-updated-endorsement-policy/): "arXiv will no longer accept institutional email addresses as the sole qualifier of endorsement for new authors."
   - 경로 1(기관 이메일 + 해당 domain 기존 논문 저자 이력) — **불가**. 첫 arXiv 제출이라 이력이 없다
   - 경로 2(해당 domain 기존 arXiv 저자에게 개인 endorsement) — **이 길뿐**
2. **endorser를 먼저 구할 필요가 없다.** arXiv 공식 문서 기준 절차: 계정을 만들고 **제출을 시작하면** endorsement 요청 메일과 **6자리 영숫자 endorsement code**가 발급되고, 그 링크를 후보에게 보내면 된다. 코드 없이 부탁하면 상대가 할 수 있는 일이 없으므로 **화면을 띄워 코드를 받아둔 뒤 연락**할 것
3. 카테고리: **cs.LG** primary, **stat.ML** cross-list. 라이선스는 TMLR 제출과 맞춰 **CC BY 4.0**
4. endorser 자격: 해당 domain에 **3개월~5년 전 사이**에 일정 편수 이상 낸 저자(편수는 분야마다 다르고 공개돼 있지 않다). **peer review가 아니다** — arXiv 문서가 명시하듯 "글이 그 카테고리에 속하는가"만 보는 절차이므로, 내용 심사를 부탁하는 것처럼 쓰지 말 것
5. endorser 후보 우선순위: ① KRAFTON AI 조직 동료(cs.LG 논문 보유 가능성 높음, 유학·이직 신호가 전혀 아님) ② Koderunner 2026 동석 패널 ③ CMPSC 465 교수 ④ 본 논문이 인용한 저자에게 콜드메일(arXiv가 공식 허용하는 방법)
6. endorsement 승인 후: `make arxiv` → `paper/arxiv/arxiv-submission.tar.gz` 업로드 → arXiv 생성 PDF 확인 → 승인
7. 게시 후: arXiv ID를 이 파일과 `docs/index.html`에 반영. **제출본 PDF에는 넣지 말 것**(위 TMLR 조건)

### arXiv 폼 입력값 (그대로 붙여넣기)

`submission_fields`와 같은 원칙: PDF에서 복사하지 말고 아래 블록을 쓴다. 초록은 `main.tex`+`numbers.tex`에서 매크로를 치환해 뽑았고, OpenReview에 낸 초록과 수식 표기만 다르고 본문이 동일함을 스크립트로 대조했다 (2026-08-31).

| 필드 | 값 |
|---|---|
| Authors | Youngmin Ko — affiliation: Pennsylvania State University |
| Title | `How Much Do Time-Series Anomaly Detection Metrics Actually Disagree? Null Models and Cluster-Aware Inference for Rank-Flip Statistics` |
| Primary category | **cs.LG** (Machine Learning) |
| Cross-list | **stat.ML** |
| License | **CC BY 4.0** (TMLR 제출과 동일) |
| Comments | `12 pages. Code and artifacts that regenerate every reported number: https://github.com/mandu5/structure-aware-tsad-evaluation` — venue명·"under review"는 **쓰지 않는다** (프리프린트에 venue를 적으면 심사자에게 링크를 하나 더 주는 셈) |
| Journal-ref / DOI / Report-no / MSC / ACM class | 전부 공란 |
| Upload | `paper/arxiv/arxiv-submission.tar.gz` (`make arxiv` 산출물, 7파일) |

**Abstract** (arXiv는 `$...$` 수식을 렌더링한다):

```
Reports that point-level and segment-level metrics rank time-series anomaly detectors differently have become a standard argument for evaluation reform. These reports take the form of a rank-flip rate: the fraction of model pairs that two metrics order differently. We audit that statistic on a 180-series, 25-model recomputation of TSB-AD-M spanning 17 source collections, and on a 6-dataset, seven-detector grid. Our main finding is that evaluation series are treated as independent when they are not, and that this invalidates the standard $\alpha$-based structural explanation built on top of the statistic. The covariate most often invoked to explain disagreement, the short-anomaly ratio $\alpha$, is constant within 11 of the 12 collections that contain more than one series: it is a collection label rather than a series-level variable. Its rank correlation with the flip rate falls from $0.3241$ at the series level to $0.0563$ ($p = 0.827$) with collections as the unit, and to $0.0898$ when one collection is removed. Interval estimates move the same way, from $[0.2979, 0.3312]$ resampling series to $[0.2695, 0.3715]$ clustering over collections; on the six-dataset grid the clustered interval spans $[0.0667, 0.4167]$, which cannot resolve its magnitude. Two further omissions point the same way. Raw flip percentages are reported without stating the chance level, which is $0.5$ and not $0$: our observed 0.3145 against a permutation null of 0.5002 means the metrics agree on 68.6% of pairs. And flips are pooled across margins: among the 13.3% of pairs that both metrics separate by at least $0.20$, a fraction of 0.0220 are ordered differently, so confident disagreement is roughly two percent rather than the 0.3145 that gets reported. We apply the audit to a composite metric we previously proposed ourselves and show it is uninformative by construction at both ends of the regime it was built to span. Applying the same corrections to our own positive findings leaves one covariate standing, segment count, at $-0.6225$ ($p = 0.008$) with collections as the unit. We give a reporting protocol and release code that regenerates every number here from committed artifacts.
```

### endorser 후보 — 본 논문 참고문헌에서 (경로 ④)

전원 최근 5년 내 cs.LG 논문이 있는 현역이라 arXiv 자격 요건은 충족한다. 위 우선순위 ①~③(KRAFTON 동료·Koderunner 패널·교수)이 안 될 때의 보강용이다.

| 후보 | 왜 | 주의 |
|---|---|---|
| Rishabh Agarwal (Google DeepMind) | `rliable`·"statistical precipice" 저자 — 이 논문의 추론 엄밀성 논지가 직접 인용하는 작업. 주제 정합성이 가장 높고 이해관계 없음 | 가장 먼저 시도할 만함 |
| Mononito Goswami (CMU) | MOMENT 저자, TSAD 벤치마킹 현역, cs.LG 활동 활발 | — |
| Sebastian Schmidl / Thorsten Papenbrock (HPI) | TimeEval — TSAD 평가 방법론 그 자체를 다룸 | — |
| Alexis Huet / Dario Rossi (Huawei) | Affiliation metrics 저자 — 본 논문이 쓰는 Aff-F1의 원저자 | 본인 지표가 분석 대상이라 반응 예측 어려움 |
| John Paparrizos / Qinghua Liu / Paul Boniol (TSB-AD) | 감사 대상 벤치마크의 저자 | **비추천을 먼저 고려** — 자기 벤치마크를 감사한 논문의 endorser가 되는 건 어색하다. 다만 endorsement는 심사가 아니므로 요청 자체는 정당함 |

### endorsement 요청 메일 (그대로 사용 가능)

한 줄 보강: 이제 실제 저널 심사 중이므로 그 사실을 넣으면 요청의 무게가 달라진다. 단 **venue 이름(TMLR)은 쓰지 말 것** — 상대가 우연히 이 논문의 심사자일 경우를 배제할 수 없고, 이름을 빼도 문장의 효력은 같다.


> **Subject:** arXiv endorsement request (cs.LG)
>
> Hi [NAME],
>
> I've written a single-author paper on evaluation methodology for time-series anomaly detection — it audits the "rank-flip rate" statistic that's become a standard argument for evaluation reform, and shows the standard structural explanation doesn't survive clustered inference. I'm posting it to arXiv.
>
> The manuscript is currently under review at a journal; posting the preprint is permitted alongside that. This is my first arXiv submission, and under the policy that changed in January 2026 an institutional email alone no longer qualifies — I need an endorsement from an existing author in the category.
>
> Would you be willing to endorse me for **cs.LG**? It's a one-click confirmation on arXiv's side. It isn't a review or a judgment on the work's quality, just a confirmation that the submission belongs in the category.
>
> My endorsement code is **KQOI4O** and the link is https://arxiv.org/auth/endorse?x=KQOI4O. Happy to send the manuscript first if you'd rather look at it.
>
> Thanks either way.
>
> Youngmin Ko

### 발송 상태 (2026-09-06)

| 후보 | 연락처 (공개 출처) | 자격 근거 | 상태 |
|---|---|---|---|
| **Rishabh Agarwal** — Periodic Labs 창립 멤버, McGill 겸임교수 (agarwl.github.io) | `rishabhagarwal.467@gmail.com` (본인 홈페이지) | 2024년 cs.LG 논문 다수 (2408.15240, 2410.11325, 2410.18252) → 3편·3개월~5년 조건 충족 | **Gmail 임시보관함에 완성 초안 있음** (`mandu00005@gmail.com`, 받는 사람·제목·본문·코드 전부 채움) — **보내기 버튼만 누르면 됨** |
| **Mononito Goswami** — Amazon Applied Scientist, 전 CMU (mononito.com) | `mononitogoswami98@gmail.com` (본인 홈페이지) | MOMENT(2402.03885)·In-context FT(2410.24087)·Foundation Model Forecasts(2510.19345) 등 cs.LG → 충족. ICLR'23 TSAD 모델선택 논문이라 주제 인접 | 아래 본문 완성 — Gmail 초안 생성은 권한 분류기에 차단됨, 직접 붙여넣어 발송 |

발송 자체는 Claude Code 권한 분류기가 막았다(외부 발신). 두 통 동시에 보내도 문제없다 — arXiv는 한 명만 승인하면 되고, 두 번째 사람이 링크를 눌러도 "이미 endorsed" 안내만 뜬다.

### 2순위 후보용 초안 (Mononito Goswami)

> **Subject:** arXiv endorsement request (cs.LG) — time-series anomaly detection evaluation
>
> Hi Mononito,
>
> I'm writing because of your ICLR 2023 work on unsupervised model selection for time-series anomaly detection — my paper sits next to it. It audits the "rank-flip rate" commonly reported between point-level and segment-level metrics (AUC-ROC vs Affiliation-F1) on TSB-AD-M and TAB, and finds that the number is usually read without its chance level (which is 0.5, not 0), that most of the residual disagreement is a margin artifact, and that the series-level covariate normally blamed for it (the short-anomaly ratio) is really a collection-level label — so the usual structural explanation does not survive cluster-aware inference. If detector rankings are the object one selects over, the paper is about how much of their instability across metrics is real.
>
> It is a single-author manuscript, currently under review at a journal (posting a preprint is permitted). This is my first arXiv submission and, since the January 2026 policy change, an institutional email alone no longer qualifies — I need an endorsement from an existing cs.LG author.
>
> Would you be willing to endorse me for cs.LG? It's a one-click confirmation on arXiv's side, not a review — just that the paper belongs in the category. My endorsement code is **KQOI4O** and the link is https://arxiv.org/auth/endorse?x=KQOI4O
>
> The manuscript (anonymized journal-submission build) and the code that regenerates every reported number are here: https://github.com/mandu5/structure-aware-tsad-evaluation (paper/main.pdf). Happy to send the named preprint build directly if that's easier.
>
> Thanks either way,
>
> Youngmin Ko
> Pennsylvania State University

### 1순위 후보용 개인화 초안 (Rishabh Agarwal) — Gmail 임시보관함과 동일 본문

> **Subject:** arXiv endorsement request (cs.LG) — a paper that leans on rliable's argument
>
> Hi Rishabh,
>
> I'm writing because a single-author paper of mine applies the argument you made in "Deep RL at the Edge of the Statistical Precipice" to a different literature: time-series anomaly detection evaluation. Its headline claim is that the widely reported "rank-flip rate" between point-level and segment-level metrics has been computed as if evaluation series were independent when they are not — series within a benchmark come from a handful of source collections — and that clustering over collections, stating the chance level, and reporting interval estimates changes what the statistic supports. The paper reads as a re-analysis in the spirit of rliable, and cites it as such.
>
> The manuscript is under review at a journal; posting the preprint is permitted alongside that. This is my first arXiv submission, and since the January 2026 policy change an institutional email alone no longer qualifies, so I need an endorsement from an existing cs.LG author.
>
> Would you be willing to endorse me for **cs.LG**? It's a one-click confirmation on arXiv's side — not a review, just a confirmation that the paper belongs in the category. My endorsement code is **KQOI4O** and the link is https://arxiv.org/auth/endorse?x=KQOI4O
>
> The manuscript (anonymized journal-submission build) and the code that regenerates every reported number are here: https://github.com/mandu5/structure-aware-tsad-evaluation (paper/main.pdf). I'm happy to send the named preprint build directly if that's easier.
>
> Thanks either way,
>
> Youngmin Ko

## DMLR 제출 패킷 (2026-09-06)

**venue 사실 (실측)**: DMLR = Journal of Data-centric Machine Learning Research, JMLR 계열. OpenReview `https://openreview.net/group?id=DMLR` → "Add: DMLR Submission". **single-blind** (data.mlr.press 명시: "single-blind review process with open reviewing") → PDF에 저자 실명·소속·저장소 URL 있음이 정상. 라이선스는 폼에 고정: **CC BY-SA 4.0**. 결정까지 통상 4~6개월. 페이지 제한 없음(현재 16p).

**필수 필드 (API 실측 `DMLR/-/Submission`)**: `title` · `abstract` · `authors` · `authorids`(OpenReview 프로필 검색, 전 저자 프로필 필수) · `pdf`(≤50MB) · `competing_interests` · `human_subjects_reporting`. 선택: `keywords` · `supplementary_material`(zip, 익명화 요구 — 안 냄) · `previous_DMLR_submission_url`/`changes_since_last_submission`(**DMLR에서** 리젝된 적 있을 때만 — TMLR 리젝은 해당 없음, 공란) · `previous_publication_url`(공란).

| 필드 | 값 |
|---|---|
| Title | (위 Title 절과 동일) |
| Abstract | (위 Abstract 절과 동일 — 본문 변경 없음) |
| Authors / Authorids | Youngmin Ko / `~YoungminKo1` |
| Keywords | `time-series anomaly detection, evaluation metrics, benchmark audit, rank-flip rate, cluster-robust inference, TSB-AD, TAB` |
| Competing Interests | TMLR 제출 때와 동일 문구 (KRAFTON 재직·한화 인턴 공개, 본 연구 무관) |
| Human Subjects Reporting | TMLR 제출 때와 동일 문구 (N/A, 공개 벤치마크 재분석) |
| PDF | `paper/main.pdf` @ `8785ec0`, sha256 `7a8e7b3b2cc1e9d3c76c49dc639700305f01269dea1a4478d078e88c3ecb955b`, 16p |

**원고에서 DMLR 템플릿 요구로 추가된 것**: `\begin{keywords}`, `\impact{}`(Broader Impact Statement), `\acks{}`(무자금·이해관계·LLM 보조 고지). 본문 수치·주장은 TMLR 제출본과 동일(`numbers.tex` 매크로 340개 그대로).

## DMLR 제출 기록

- **일시**: 2026-09-06 (KST, 밤), OpenReview 확인 문구 "Your submission is complete. Check your inbox for a confirmation email. The author console page for managing your submissions will be available soon."
- **Venue**: DMLR (Journal of Data-centric Machine Learning Research), rolling, single-blind
- **저자**: `~YoungminKo1` 단독 (폼 자동 등록)
- **업로드 PDF**: `paper/main.pdf` @ `8785ec0` — sha256 `7a8e7b3b2cc1e9d3c76c49dc639700305f01269dea1a4478d078e88c3ecb955b`, 16p (서버 경로 `/pdf/c8f2703ab31c2d40e670ea7095b4944ff7266ca1.pdf`)
- **License**: CC BY-SA 4.0 (폼 고정)
- **입력값**: 위 패킷과 동일 (Title / Abstract TeX 수식 포함 / Keywords 7개 / Competing Interests·Human Subjects는 TMLR 때 문구)
- **Submission Number: 252** — forum `5pcDaNOVvR`, https://openreview.net/forum?id=5pcDaNOVvR (상태 "Submitted to DMLR", 공개 범위 `DMLR / Action Editors / Authors`)
- Author console: https://openreview.net/group?id=DMLR/Authors (제출 직후엔 미활성, OpenReview 검색으로 forum 확인)
- 확인 메일은 OpenReview Preferred 주소(네이버)로 감

## 제출 기록

- **일시**: 2026-08-31 (KST), OpenReview 확인 문구 "Your submission is complete."
- **Venue**: TMLR (Transactions on Machine Learning Research), rolling submission
- **저자**: `~YoungminKo1` 단독
- **업로드 PDF**: `paper/main.pdf` — SHA256 `59520383a374ddfab6437a3c597529a565fee6f4f6db1506a3bc30c1f1665de0` (커밋본과 동일)
- **Submission Type**: Regular submission (본문 12p 이하)
- **License**: CC BY 4.0
- **Submission Number**: 11830
- **Forum URL**: https://openreview.net/forum?id=xHEQJedMZ9 (forum id `xHEQJedMZ9`)
- **Author console**: https://openreview.net/group?id=TMLR/Authors
- **상태 확인 2026-08-31**: 포럼에 "Submitted to TMLR" 표시, 공개 범위 `TMLR / Action Editors / Authors`, License `CC BY 4.0`. Author console 기준 `0 Reviews Submitted / 0 Recommendations`, Decision Status `No Recommendation` — AE 배정 전 정상 대기 상태이며 결함 신호가 아니다.
- **주의**: OpenReview 계정 이메일이 `mandu00005@gmail.com`이 아니다(해당 Gmail에 OpenReview 메일 이력 0건). 제출 확인·심사 통보 메일은 다른 주소로 가므로 그 계정을 확인할 것.

### 🔴 결과: 데스크 리젝 (2026-09-06 19:35 KST)

- 포럼 상태 `Desk rejected by TMLR`. 노트 "Desk Rejection by Editors In Chief (Gautam Kamath, Naila Murray, Nihar B Shah, Laurent Charlin, +1 more)", **본문 비어 있음**. AE·리뷰어 배정 전 편집장단 단계에서 걸러짐 (제출 6일 만). TSAD 세션이 2026-09-06 포럼에서 직접 확인.
- 통보 메일(네이버) 요지: "rejected without further review. It was deemed to be unlikely to meet one or both of TMLR criterion and could not be sent for further review due to high volume of submissions and scarce bandwidth of the volunteer reviewers and AEs." 개별 사유 없음.
- TMLR 기준 2개: ① 주장이 정확·설득력 있는 근거로 뒷받침되는가 ② TMLR 독자 일부라도 관심을 가질 결과인가. 어느 쪽에 걸렸는지는 알 수 없다.
- TMLR 정책상 재투고는 가능(새 제출 + 이전 제출 링크 + 변경 내역)하나, 볼륨 사유 데스크 리젝을 같은 원고로 다시 넣는 건 의미 없다.
- 부수 사실: 이 제출 때문에 걸어 둔 익명성 제약(공개 페이지에 새 제목 병기 금지)은 **재투고처가 정해질 때까지 유지**. 단 DMLR처럼 single-blind 저널로 가면 제약이 사라진다.

**재투고 후보 (2026-09-06 조사)**

| 후보 | 근거 | 제약 |
|---|---|---|
| **DMLR** (Journal of Data-centric ML Research, JMLR 계열) — **권고** | 명시 범위에 "Benchmarking tools and methods", "dataset audits", "Systematic analyses of existing systems on … benchmarks that yield important new insight" — 이 논문 그 자체. OpenReview 롤링, **single-blind**, arXiv 병행 허용, 페이지 제한 없음 | 전용 LaTeX 템플릿 필수(`github.com/JmlrOrg/dmlr-style-file`) → 재조판. 결정까지 4~6개월 |
| ICLR 2027 | 평가 방법론·통계 엄밀성 논문 수요 있음 | **abstract 9/18, paper 9/25 AoE** — 12일. 본문 9p로 압축 필요. 결정 12/16이라 석사 원서(12/1~15)에는 "under review"로만 |
| TMLR 재투고 | 정책상 가능 | 같은 원고면 같은 결과. 실질적 재구성이 없으면 비추 |

### 폼에서 실제로 확인된 것 — README 체크리스트 보완

README §5는 필수 폼 필드를 `competing_interests`·`human_subjects_reporting` 2개로 적었으나, 실제 폼에는 **필수 필드가 2개 더** 있었다:

- **Submission Type\*** — Regular / Long / Beyond PDF 중 택1
- **License\*** — CC BY 4.0 (단일 선택지이나 필수)

또한 `Previous TMLR Submission Url`과 `Changes Since Last Submission`은 **TMLR에 이전 제출이 있을 때만** 쓰는 칸이다. NeurIPS 리젝은 여기 해당하지 않으므로 공란으로 두었다.

### Competing Interests — "None"으로 내지 않은 이유

폼 안내문이 명시적으로 요구한다: *"disclose relationships (notably financial) of any author with entities… **during the last 36 months**… This would include **engagements with commercial companies** (sabbaticals, **employments**, stipends)…"*

KRAFTON 재직(2026-06~)과 한화에어로스페이스 인턴(2026-01~02)이 여기 해당하므로 **둘 다 공개**하고, 두 소속이 본 연구를 후원·의뢰·검토하지 않았음을 명시했다.

**익명성 영향 없음**: 이 필드의 공개 범위는 폼에서 `TMLR / TMLR Paper number Action Editors / TMLR Paper number Authors`로 표시된다 — **심사자(Reviewers)는 포함되지 않는다.** 소속을 적어도 이중맹검이 깨지지 않는다. `human_subjects_reporting`도 동일한 범위다.
