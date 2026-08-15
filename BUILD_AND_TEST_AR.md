# دليل بناء واختبار LanguageBarrier RTL على Windows

## المتطلبات

يحتاج المشروع إلى Windows 10 أو أحدث، وVisual Studio 2022 مع workload باسم **Desktop development with C++**، وWindows SDK، وملفات MSVC x86. يجب أن يكون الهدف `Win32` لأن ملف المشروع لا يبني DLL بمعمارية x64.

يحتاج المشروع أيضاً إلى vcpkg حتى تُبنى الاعتماديات المحددة في `vcpkg.json`: MinHook وDirectXTex وFreeType وnlohmann-json وCereal وImGui وbetter-enums. لا تستخدم نسخة DLL من منصة مختلفة عن اللعبة؛ لعبة Steins;Gate القديمة تحتاج عادةً DLL ‏32-bit.

## البناء عبر Developer Command Prompt

افتح **x86 Native Tools Command Prompt for VS 2022**، وانتقل إلى مجلد المشروع المعدل:

```bat
cd /d C:\path\to\LanguageBarrier-main
```

إذا لم يكن vcpkg مثبتاً، ثبّته بالطريقة المعتادة ثم فعّل تكامل MSBuild:

```bat
git clone https://github.com/microsoft/vcpkg C:\vcpkg
C:\vcpkg\bootstrap-vcpkg.bat
C:\vcpkg\vcpkg integrate install
```

بعد ذلك افتح الحل أو ابنِه مباشرةً:

```bat
msbuild LanguageBarrier.sln /m /p:Configuration=dinput8-Release /p:Platform=Win32
```

لنسخة Debug:

```bat
msbuild LanguageBarrier.sln /m /p:Configuration=dinput8-Debug /p:Platform=Win32
```

الناتج المتوقع هو `dinput8.dll` داخل مجلد `bin` أو مجلد الإخراج الذي يحدده Visual Studio. إعدادات `cryptbase-Release` و`cryptbase-Debug` تنتج `cryptbase.dll` بدلاً من `dinput8.dll`، ولا ينبغي اختيارها إلا إذا كان patch المستهدف يستخدم طريقة تحميل cryptbase.

إذا فشل MSBuild في إيجاد الاعتماديات، نفّذ بناء vcpkg للـ triplet x86 ثم أعد المحاولة:

```bat
C:\vcpkg\vcpkg install --triplet x86-windows
msbuild LanguageBarrier.sln /m /p:Configuration=dinput8-Release /p:Platform=Win32 /p:VcpkgEnabled=true
```

في بعض تثبيتات Visual Studio يكون اسم المنصة في الحل `Win32` لكن vcpkg يستخدم `x86-windows`. هذا طبيعي؛ الأول يحدد معمارية MSBuild والثاني يحدد معمارية حزم vcpkg.

## تفعيل الوضع

في ملف patch configuration الخاص بنسخة اللعبة، أضف:

```json
{
  "patch": {
    "rtlDialogue": true,
    "rtlDialogueRightX": 1200,
    "rtlDialogueKeepNameLine": true,
    "rtlDialogueReverseText": true
  }
}
```

يجب إبقاء `rtlDialogue` مفعلاً فقط أثناء الاختبار. الكود يقرأ الخيارات عند `gameTextInit()`، ثم يركّب hooks `drawDialogue` و`drawDialogue2` لمسار الحوار العام حتى لو كان `improveDialogueOutlines` غير مفعّل. إذا كان `rtlDialogueReverseText` مفعلاً، يبدّل hook مصدر glyph داخل صفحة الحوار فقط، ثم يطبق mirror X القديم. لا يغيّر السكربت أو Backlog أو النصوص العامة.

## ترتيب الاختبار

انسخ DLL الناتج إلى مجلد اللعبة وفق طريقة patch الأصلية، واحتفظ بنسخة احتياطية من DLL والملفات الأصلية. لا تختبر فوق ملف الحفظ الوحيد؛ استخدم مشهداً قصيراً يمكن تكراره.

ابدأ بجملة عربية قصيرة من كلمتين أو ثلاث. اختبر أولاً `rtlDialogueReverseText=false` لمقارنة RTL وحده، ثم اختبر `rtlDialogueReverseText=true`. في الوضع الثاني يجب أن تتبدل هوية glyphs داخل الحوار فقط مع بقاء موضع slot وأبعاده ثابتة، ثم يظهر السطر من اليمين إلى اليسار. كما يجب أن تستخدم حركة الكتابة التدريجية `opacity` الخاصة بالـ glyph المرئي نفسه؛ أي يظهر أول glyph منطقي أولاً من جهة اليمين، ثم تمتد الكتابة إلى اليسار. لا تغيّر ترتيب النص في الملفات ولا تفعل reverse خارج DLL أثناء هذه المقارنة.

بعد ذلك اختبر سطراً طويلاً يلتف إلى سطرين. في كل سطر يجب أن يبقى اتجاه الإضافة من اليمين إلى اليسار. راقب الحركة أثناء أول ثواني من ظهور الجملة، لا الإطار النهائي فقط. اختبر أيضاً اسم المتحدث، لأن hook العام قد يشمله إذا كان مخزناً في نفس DialoguePage. ثم اختبر الانتقال إلى الجملة التالية للتأكد من عدم وجود تداخل؛ التعديل الحالي لا يغير Backlog أو mail عمداً.

## قراءة النتيجة

| النتيجة | التفسير المحتمل |
|---|---|
| لا يوجد تغيير إطلاقاً | DLL غير محمّل، أو patch يستخدم configuration آخر، أو signatures لا تطابق executable |
| النص يبدأ يميناً وينتشر يساراً لكن الكلمات متصلة خطأ | اتجاه الإحداثيات يعمل، لكن هناك حاجة إلى shaping؛ هذا ليس عكساً للنص |
| الإطار النهائي صحيح لكن الظهور التدريجي يبدأ من الطرف الخطأ | تأكد أن DLL الجديد يحتوي `charDisplayOpacity[renderIndex]`، وأن السجل يقرأ `reverseText=1` |
| اتجاه RTL صحيح لكن المحتوى معكوس | فعّل `rtlDialogueReverseText=true` داخل الحوار فقط، ولا تعكس النص في السكربت أثناء الاختبار |
| السطر الثاني غير صحيح | حدود الأسطر التي تبنيها اللعبة لا تتوافق مع شرط Y الحالي؛ نحتاج تعديل helper ليستخدم معلومات line-break الأصلية |
| crash عند بدء اللعبة | DLL أو configuration غير متوافق، أو signature خاطئة؛ أعد DLL الأصلي وافحص `languagebarrier\log.txt` |

## فحص السجل

بعد التشغيل، راجع:

```text
languagebarrier\log.txt
```

تأكد من ظهور اسم اللعبة واسم patch وعدم وجود فشل في `drawDialogue` أو signature scanning. يجب أن يظهر أيضاً سطر يبدأ بـ `RTL dialogue config:` وينتهي بقيمة `reverseText=1` عند تفعيل الخيار. إذا لم يصل التنفيذ إلى hook، أرسل ملف السجل وملف `gamedef.json` المستخدم، لأن الأرشيف الحالي يحتوي core العام ولا يحتوي signatures الخاصة بإصدار Steins;Gate عند المستخدم.

## حدود النسخة الحالية

هذه النسخة لا تقلب النص ولا تنفذ shaping، وهو مناسب للحالة التي يكون فيها السكربت الياباني مجرد مصدر glyph IDs وتكون الترجمة العربية جاهزة بالتشكيل في الخط أو في طبقة patch الأخرى. التعديل يغيّر مواضع الرسم فقط ويحافظ على ترتيب الحلقة وكشف النص. بناء DLL فعلي لم يتم داخل بيئة Ubuntu الحالية لغياب MSVC وWindows SDK؛ يجب تنفيذ الأوامر أعلاه على Windows أو عبر بيئة Visual Studio متوافقة.
