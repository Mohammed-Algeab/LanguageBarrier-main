# بناء LanguageBarrier عبر GitHub Actions

## الفكرة

لا ترفع ملف ZIP نفسه إلى GitHub بهدف البناء. يجب فك الضغط ثم رفع **محتويات المشروع** إلى مستودع GitHub جديد، مع الحفاظ على المجلد المخفي `.github/workflows/build.yml`. هذا الملف هو الذي يطلب من GitHub تشغيل Windows وVisual Studio وبناء DLL تلقائياً.

## الطريقة الأسهل باستخدام GitHub Desktop أو Git Bash

أنشئ مستودعاً جديداً وفارغاً في GitHub، ثم فك ضغط `LanguageBarrier-main-rtl-flow.zip` على جهازك. تحتوي هذه النسخة على خيار `rtlDialogueFlowRTL` الجديد.
 افتح PowerShell أو Git Bash داخل المجلد الذي يحتوي على `LanguageBarrier.sln`، وليس داخل مجلد فرعي زائد اسمه `LanguageBarrier-main` إذا كان سيجعل الحل في مكان خاطئ.

نفّذ الأوامر التالية بعد استبدال عنوان المستودع بعنوان مستودعك:

```bash
git init -b main
git add .
git commit -m "Add RTL LanguageBarrier build"
git remote add origin https://github.com/USERNAME/REPOSITORY.git
git push -u origin main
```

بعد الرفع، افتح تبويب **Actions** في المستودع. ستجد workflow باسم **Build LanguageBarrier RTL**. سيبدأ تلقائياً عند push إلى فرع `main`، ويمكن تشغيله يدوياً من **Actions → Build LanguageBarrier RTL → Run workflow**.

بعد تنزيل الـ DLL، استخدم في `patchdef.json` الإعداد `rtlDialogueMirrorGlyphs: false` مع `rtlDialogueFlowRTL: true` إذا كانت glyphs في السكربت معكوسة مسبقاً من أجل Backlog. لا تحتاج إلى إعادة بناء DLL عند تغيير قيم `rtlDialogueRightX` أو أي خيارات RTL؛ عدّل patchdef فقط.

## تنزيل DLL

عندما تنتهي العملية بنجاح، افتح تشغيل workflow ثم انزل إلى قسم **Artifacts**. نزّل الملف الذي اسمه قريب من:

```text
LanguageBarrier-dinput8-Release
```

فك ضغط artifact. يجب أن تجد داخله `dinput8.dll` ومجلد `languagebarrier` و`VSFilter.dll` أو الملفات المرافقة التي نسخها المشروع أثناء البناء. لا تستخدم ملف `dinput8.dll` وحده إذا كان مجلد `languagebarrier` موجوداً؛ انسخ مجموعة الناتج كما هي إلى مجلد اللعبة وفق تعليمات patch Committee of Zero.

## إذا لم يظهر workflow

تحقق من أن المسار داخل المستودع هو بالضبط:

```text
.github/workflows/build.yml
```

وليس:

```text
LanguageBarrier-main/.github/workflows/build.yml
```

إذا ظهر مجلد `LanguageBarrier-main` كطبقة إضافية في المستودع، انقل الملفات الموجودة داخله إلى جذر المستودع بحيث يكون `LanguageBarrier.sln` في المستوى الأعلى، ويكون `.github` في المستوى الأعلى أيضاً.

## إذا فشل البناء

افتح تشغيل workflow الفاشل، وانسخ أول رسالة خطأ حمراء كاملة. الأخطاء الأكثر فائدة للتشخيص هي فشل `vcpkg install`، أو عدم إيجاد `VSFilter.lib`، أو عدم إيجاد `LanguageBarrier.sln`، أو فشل signature ليس من مرحلة البناء بل يظهر فقط عند تشغيل اللعبة.

لا تحتاج إلى إضافة API key أو secret لهذا workflow؛ الاعتماديات العامة وVisual Studio تُثبت داخل runner. لكن GitHub Actions قد يتطلب تفعيل Actions في المستودع، وقد يفرض حدوداً على الدقائق المتاحة للحساب المجاني.

## اختيار cryptbase بدلاً من dinput8

النسخة الحالية تبني `dinput8-Release` افتراضياً، وهو الاختيار المعتاد لهذا المسار. إذا كان patch الخاص بك يطلب `cryptbase.dll`، افتح `.github/workflows/build.yml` وأزل علامة التعليق عن السطر:

```yaml
# - cryptbase-Release
```

ثم أعد التشغيل. سيُنشئ workflow artifact إضافياً باسم `LanguageBarrier-cryptbase-Release`.
