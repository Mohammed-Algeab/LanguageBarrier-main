# بناء LanguageBarrier عبر GitHub Actions

## الفكرة

لا ترفع ملف ZIP نفسه إلى GitHub بهدف البناء. يجب فك الضغط ثم رفع **محتويات المشروع** إلى مستودع GitHub جديد، مع الحفاظ على المجلد المخفي `.github/workflows/build.yml`. هذا الملف هو الذي يطلب من GitHub تشغيل Windows وVisual Studio وبناء DLL تلقائياً.

## الطريقة الأسهل باستخدام GitHub Desktop أو Git Bash

أنشئ مستودعاً جديداً وفارغاً في GitHub، ثم فك ضغط `LanguageBarrier-main-rtl.zip` على جهازك. افتح PowerShell أو Git Bash داخل المجلد الذي يحتوي على `LanguageBarrier.sln`، وليس داخل مجلد فرعي زائد اسمه `LanguageBarrier-main` إذا كان سيجعل الحل في مكان خاطئ.

نفّذ الأوامر التالية بعد استبدال عنوان المستودع بعنوان مستودعك:

```bash
git init -b main
git add .
git commit -m "Add RTL LanguageBarrier build"
git remote add origin https://github.com/USERNAME/REPOSITORY.git
git push -u origin main
```

بعد الرفع، افتح تبويب **Actions** في المستودع. ستجد workflow باسم **Build LanguageBarrier Arabic dialogue**. سيبدأ تلقائياً عند push إلى فرعي `main` أو `master`، ويمكن تشغيله يدوياً من **Actions → Build LanguageBarrier Arabic dialogue → Run workflow**. النسخة الحالية لا تستخدم `microsoft/setup-msbuild` ولا `ilammy/msvc-dev-cmd`؛ بل تكتشف Visual Studio وMSBuild و`VsDevCmd.bat` المثبتة مسبقًا في runner `windows-2022`، لتجنب فشل تنزيل الأكشن من `codeload.github.com`.

## تنزيل DLL

عندما تنتهي العملية بنجاح، افتح تشغيل workflow ثم انزل إلى قسم **Artifacts**. نزّل artifact الخاص بإعداد `dinput8-Release` واسمه:

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

افتح تشغيل workflow الفاشل، وانسخ أول رسالة خطأ حمراء كاملة. إذا ظهر خطأ `429 Too Many Requests` أو `503 Service Unavailable` من `codeload.github.com/microsoft/setup-msbuild`، فهذا يعني أن نسخة قديمة من workflow ما زالت تعمل؛ تأكد من push لملف `.github/workflows/build.yml` الجديد ثم أعد تشغيل أحدث commit. في النسخة الحالية تُفحص أولاً ملفات Visual Studio عبر `vswhere.exe`، ثم تظهر أخطاء البناء الفعلية فقط إذا فشل `vcpkg install` أو لم توجد `VSFilter.lib` أو لم يوجد `LanguageBarrier.sln`.

لا تحتاج إلى إضافة API key أو secret لهذا workflow؛ Visual Studio وMSBuild وVC tools موجودة مسبقًا في `windows-2022`، بينما يجلب workflow vcpkg والاعتماديات المطلوبة. يستخدم الحل `/p:Platform=x86` على مستوى الـsolution، ويحوّل المشروع داخليًا إلى Win32، بينما يستخدم vcpkg triplet `x86-windows-static-md`. قد يتطلب GitHub Actions تفعيل Actions في المستودع، وقد يفرض حدودًا على الدقائق المتاحة للحساب المجاني.

## اختيار cryptbase بدلاً من dinput8

النسخة الحالية تبني `dinput8-Release` افتراضياً، وهو الاختيار المعتاد لهذا المسار. إذا كان patch الخاص بك يطلب `cryptbase.dll`، افتح `.github/workflows/build.yml` وأزل علامة التعليق عن السطر:

```yaml
# - cryptbase-Release
```

ثم أعد التشغيل. سيُنشئ workflow artifact إضافياً باسم `LanguageBarrier-cryptbase-Release`.
