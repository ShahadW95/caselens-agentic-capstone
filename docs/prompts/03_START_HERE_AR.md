---
title: "CASE//LENS — ابدؤوا من هنا"
purpose: "تشغيل الحزمة وتقسيم العمل بين Codex وClaude Code"
status: "v1.1 — تحديث قضية بيرني ميدوف"
---

# CASE//LENS — ابدؤوا من هنا

هذا الملف ليس برومبت بناء. هو خريطة تشغيل سريعة تمنع تضارب الشغل بينكما. مصدر الحقيقة التقني الكامل هو `00_CASELENS_MASTER_CONTEXT.md`، ثم تنفذ كل واحدة ملف مسارها فقط.

## ملفات الحزمة

| الملف | من يقرأه؟ | وظيفته |
|---|---|---|
| `00_CASELENS_MASTER_CONTEXT.md` | أنتما + Codex + Claude Code | تعريف المنتج، النظام، الوكلاء، العقود، الأمان، GitHub، والمعايير |
| `01_SHAHAD_CODEX_TRACK.md` | شهد + Codex | التأسيس، العقود، الحالة والذاكرة، Supervisor، LangGraph، المراجع، الواجهة، الدمج، التسليم |
| `02_TEAMMATE_CLAUDE_TRACK.md` | الزميلة + Claude Code | المصادر، بيانات القضية، RAG، الأدوات، الوكلاء المتخصصون، واختبارها |
| `03_START_HERE_AR.md` | أنتما | ترتيب البدء والتزامن والمتابعة |
| `04_MADOFF_CASE_BLUEPRINT_AR.md` | أنتما | التصور العربي للقضية، حدودها، بياناتها، أسئلة الديمو، ومصادرها |

## القرارات المجمدة للمشروع

افتحوا Issue اسمها `D0 — Project decisions` وانسخوا القرار المعتمد:

```text
CASE//LENS D0 DECISIONS
Team: LensLab
Project: CASE//LENS — Beyond the Verdict
Closed case: United States v. Bernard L. Madoff — BLMIS Ponzi-scheme criminal case
Case ID: US_SDNY_09CR00213_DC
Jurisdiction: United States adversarial common-law system; federal criminal proceeding in S.D.N.Y.; guilty plea and sentencing
Authoritative final-status source: DOJ SDNY case page — guilty plea to all 11 counts on 2009-03-12 and 150-year sentence on 2009-06-29
Source cutoff: 2026-02-27; criminal guilt closed, victim recovery/SIPA liquidation tracked separately by as-of date
Runtime LLM: Google Gemini Developer API / gemini-3.7-flash
Embedding: gemini-embedding-2 / 768 dimensions
UI: bilingual; Arabic default with English toggle
Shahad GitHub: ShahadW95
Teammate: Zahra
Zahra GitHub: PENDING
Repository: https://github.com/ShahadW95/caselens-agentic-capstone (planned)
Demo: target 6 minutes; allowed 5–7
Deployment: yes, Streamlit Community Cloud after local MVP passes
```

لا تختاروا موديلًا بالذاكرة أو بالتخمين. افصلوا بين:

- Codex وClaude Code: مساعدان لكتابة المشروع.
- Runtime LLM: النموذج الذي سيستدعيه تطبيق CASE//LENS عندما يعمل.
- Embedding model: النموذج الذي يبني تمثيلات البحث للـRAG.

تم التحقق من اسمي النموذجين في وثائق Google الرسمية. مع ذلك، أول اختبار تقني بعد A0 هو تشغيل connection check على مفتاح شهد لأن الإتاحة والحدود الفعلية مرتبطة بالمشروع داخل Google AI Studio. الاختبارات العادية تظل على fake clients ولا تستهلك API.

ملاحظة مهمة: النموذجان متاحان حاليًا ضمن Free Tier، لكن حدود الطلبات الفعلية تظهر داخل Google AI Studio وقد تختلف حسب المشروع. بيانات Free Tier قد تستخدمها Google لتحسين منتجاتها؛ لذلك لا يرسل التطبيق إلا أسئلة عن قضية عامة وملخصات مصادر قضائية عامة، ولا يرسل أسرارًا أو بيانات شخصية.

## لماذا اخترنا قضية بيرني ميدوف؟

- هي قضية احتيال مالي ذات صدى عالمي، وآلية مخطط بونزي فيها مفهومة بصريًا: أموال مستثمرين جدد استُخدمت لتغطية طلبات وعوائد مستثمرين سابقين، بينما كانت سجلات التداول الاستثمارية الأساسية ملفقة.
- استمر الاحتيال لعقود، وانتهى بانهيار واضح خلال أزمة 2008، ثم اعتراف واتهامات وإقرار بالذنب وحكم 150 سنة؛ لذلك تعطينا Timeline قويًا ومكتملًا.
- لا تحتاج صورًا عنيفة أو تفاصيل صادمة، وتجمع بين الجريمة، المال، القانون، الرقابة، علم الثقة، والتفكير النقدي.
- فيها مفارقة ممتازة: ميدوف لم يكن موظفًا حكوميًا، لكنه شغل مناصب مؤثرة في NASD/NASDAQ وشارك في لجنة استشارية للـSEC. وفي المقابل، وثّق المفتش العام للـSEC شكاوى وإنذارات وفرصًا ضائعة للتحقق من المخطط.
- فيها Claim Check مثالي: عبارة «سرق 65 مليار دولار كاش» مضللة؛ الرقم الكبير المتداول يرتبط بالأرصدة الورقية الوهمية، بينما خسارة أصل الأموال، والمصادرة، والمبالغ المستردة، والتوزيعات أرقام مختلفة يجب عدم خلطها.
- تسمح بـWhat If واقعي ومقيّد: ماذا لو تحققت SEC من التداولات عبر طرف مستقل بعد شكوى مبكرة؟ يشرح النظام الأثر المحتمل على فرصة الاكتشاف وقوة الدليل، من دون ادعاء تاريخ بديل مؤكد أو مبلغ خسائر كان سيوفَّر.

حدود النسخة الأولى: نغطي القضية الجنائية ضد Bernard Madoff فقط. نذكر القضايا المرتبطة عند الحاجة لتصحيح ادعاء محدد مثل «عمل وحده تمامًا»، لكن لا نحوّل المشروع إلى موسوعة لكل المتهمين. القضية الجنائية مغلقة؛ أما استرداد وتعويض الأموال فهو مسار منفصل، وقد يظل جاريًا، ويجب أن يظهر بحالة وتاريخ تحديث مستقلين.

المصادر الأولية المعتمدة موجودة في ملف الـMaster، وأقواها صفحة القضية لدى وزارة العدل، مواد FBI، تقرير المفتش العام للـSEC، وسجلات SIPC. لا تدخلوا المسلسلات أو البودكاست أو تحليلات السوشال ميديا في RAG الأساسي.

## تجهيز GitHub مرة واحدة — تنفذه شهد

1. إنشاء Public Repository باسم `caselens-agentic-capstone`.
2. إضافة الزميلة Collaborator.
3. وضع ملفات الحزمة داخل `docs/prompts/` ورفعها إلى `main`.
4. إنشاء GitHub Project بنمط Board بالأعمدة:
   `Todo` → `In Progress` → `In Review` → `Blocked` → `Done`.
5. إنشاء Issues الموجودة في جدول القسم 16 من ملف الـMaster.
6. تعيين Owner واحد لكل Issue.
7. تفعيل GitHub Actions بعد Prompt A0؛ منه ستظهر نتيجة الاختبارات تلقائيًا داخل كل Pull Request.

لا تحتاجون تطبيق مهام منفصل. الـProject يعرض حالة كل جزء، الـIssue يشرح المطلوب، الـPR يعرض التغيير والمراجعة، وCI يعرض نجاح أو فشل الاختبارات.

## البداية المتزامنة

### شهد + Codex

```bash
git clone <REPOSITORY_URL>
cd caselens-agentic-capstone
git switch -c foundation/shared-contracts
```

ثم:

1. تلصق Session Header من ملف Track A.
2. تنفذ `PROMPT A0` فقط.
3. تراجع النتيجة، تشغل الاختبارات، تعمل commit وpush.
4. تفتح PR يكتب في وصفه `Closes #<A0 issue>`.
5. تنقل البطاقة إلى `In Review`.

### الزميلة + Claude Code — في الوقت نفسه

```bash
git clone <REPOSITORY_URL>
cd caselens-agentic-capstone
git switch -c research/case-source-pack
```

ثم:

1. تلصق Session Header من ملف Track B.
2. تنفذ `PROMPT B0` فقط.
3. تعمل داخل المصادر والبيانات البحثية فقط؛ لا تكتب Python قبل دمج A0.
4. تراجع المصادر، تعمل commit وpush.
5. تفتح PR يكتب في وصفه `Closes #<B0 issue>`.
6. تنقل البطاقة إلى `In Review`.

بهذا A0 وB0 يعملان فعلًا في نفس الوقت ومن دون تعديل الملفات نفسها.

## بوابة العقود — التزامن الوحيد الإجباري

بعد مراجعة ودمج A0:

- تصبح `contracts.py` و`protocols.py` هي الاتفاق الثابت بين النظامين.
- زميلتك تحدّث فرعها من `main` ثم تبدأ B1.
- أنتِ تبدأين A1 وA2 ضد Fake Specialists تطابق العقود.
- زميلتك تبني Real Specialists تطابق العقود نفسها.

إذا احتاجت زميلتك تعديل عقد، لا تعدله مباشرة. تفتح Issue بلابل `contract-change`، تشرح التغيير، توافقان عليه، ثم أنتِ تعدلين العقد في PR صغير. هذا يمنع إصلاح جزء وكسر الجزء الآخر بصمت.

## العمل المتوازي بعد بوابة العقود

| شهد + Codex | الزميلة + Claude Code | هل يوجد انتظار؟ |
|---|---|---|
| A1: state + memory + routing with fakes | B1: normalized data + validator | لا |
| A2: LangGraph + bounded reviewer | B2: Agentic RAG | لا |
| A3: functional unstyled Streamlit | B3: deterministic tools | لا |
| اختبارات ومسار فشل للواجهة | B4: real specialists | لا |
| A4: integration | B5: backend handoff/review | نعم، بوابة دمج واحدة |
| A5: README/demo/rubric audit | مراجعة وثائق ومصادر | معًا |
| A6: visual UI polish | لا توسع Backend | بعد نجاح I0 فقط |

## كيف يظهر إنجاز كل جزء «في اللحظة»؟

عند نهاية كل Prompt، تنفذ صاحبة الجزء هذا التسلسل:

1. تشغل أوامر Acceptance Evidence الموجودة أسفل البرومبت.
2. تعمل commit واضحًا، مثل:

```bash
git add <ONLY_REVIEWED_FILES>
git commit -m "feat(rag): add bounded evidence retrieval"
git push -u origin <CURRENT_BRANCH>
```

3. تحدث الـDraft Pull Request.
4. تضيف تعليق `CHECKPOINT HANDOFF` الموجود في ملف الـMaster.
5. تنقل الـIssue من `In Progress` إلى `In Review`.
6. تنتظر ظهور CI أخضر داخل الـPR.
7. الثانية تراجع diff والاختبارات، ثم توافق أو تطلب تعديلًا.
8. بعد الدمج، تغلق الـIssue/ينغلق عبر `Closes #N` وتنقل البطاقة إلى `Done`.

قاعدة مهمة: لا تكتبا «خلص» في الواتساب فقط. GitHub هو سجل الحالة الوحيد؛ الواتساب للتنبيه على blocker عاجل فقط.

## التحديث من عمل الثانية بأمان

قبل بداية checkpoint جديد:

```bash
git status
git fetch origin
git switch <YOUR_BRANCH>
git merge origin/main
pytest -q
```

إذا ظهر conflict في ملف تملكه الثانية، لا تختاري نسخة عشوائيًا ولا تستخدمي force push أو `git reset --hard`. اكتبي blocker في الـIssue وحددا من يحل الملف.

## ترتيب الدمج

1. prompt pack + D0 decisions.
2. A0 foundation/contracts.
3. B0 source pack.
4. Track B backend: B1–B5.
5. Track A integration: A1–A4.
6. A5 documentation/demo audit.
7. A6 visual design إن بقي وقت.
8. محاولة النشر على Streamlit Community Cloud بعد نجاح النسخة المحلية فقط.

يمكن أن تبقى PRs الميزات Draft أثناء العمل. لا تدمجوا Backend أو Integration إذا الاختبارات حمراء أو العقود مختلفة.

## ما يؤجل إلى النهاية؟

- الألوان، الخطوط، الرسوم، الحركة، والهوية البصرية.
- دعم أكثر من قضية.
- البحث الحي في الإنترنت.
- تسجيل المستخدمين وقاعدة بيانات سحابية.
- النشر العام.

النسخة الناجحة أولًا: قضية مغلقة واحدة، سؤال مدعوم بالمصادر، Timeline بأربعة مسارات، Claim Check يفرّق بين أنواع المبالغ، Explain the Judgment، What If? مقيّد، تفويض وكلاء ظاهر وآمن، وحالة فشل واضحة.

## روابط GitHub الرسمية

- GitHub Projects: https://docs.github.com/en/issues/planning-and-tracking-with-projects
- Issues and linked work: https://docs.github.com/en/issues/tracking-your-work-with-issues/learning-about-issues/about-issues
- Python tests in GitHub Actions: https://docs.github.com/en/actions/tutorials/build-and-test-code/python
- Keeping a PR branch updated: https://docs.github.com/en/pull-requests/how-tos/create-pull-requests/keeping-your-pull-request-in-sync-with-the-base-branch
