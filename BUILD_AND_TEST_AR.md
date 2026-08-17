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
msbuild LanguageBarrier.sln /m /p:Configuration=dinput8-Debug /p:Platform=x86
```

الناتج المتوقع هو `dinput8.dll` داخل مجلد `bin` أو مجلد الإخراج الذي يحدده Visual Studio. إعدادات `cryptbase-Release` و`cryptbase-Debug` تنتج `cryptbase.dll` بدلاً من `dinput8.dll`، ولا ينبغي اختيارها إلا إذا كان patch المستهدف يستخدم طريقة تحميل cryptbase.

إذا فشل MSBuild في إيجاد الاعتماديات، نفّذ بناء vcpkg للـ triplet x86 ثم أعد المحاولة. لا تنشئ `LanguageBarrier/contrib/lib/Release` يدويًا؛ النسخة الحالية تستخدم `contrib/lib/xy-vsfilter`، وقد أزيل مسار Release القديم من إعدادات Release في ملف المشروع لأن المستودع لا يحتوي مكتبات فعلية فيه:

```bat
C:\vcpkg\vcpkg install --triplet x86-windows-static-md
msbuild LanguageBarrier.sln /m /p:Configuration=dinput8-Release /p:Platform=x86 /p:VcpkgUserTriplet=x86-windows-static-md /p:VcpkgEnabled=true
```

في هذا الحل تحديدًا، اسم المنصة في `LanguageBarrier.sln` هو `x86`، بينما mapping داخل ملف الحل يوجهها إلى مشروع `LanguageBarrier.vcxproj` بمنصة `Win32`. لذلك يجب استعمال `/p:Platform=x86` عند بناء ملف `.sln`. أما vcpkg فيستخدم `x86-windows-static-md` لتحديد معمارية الحزم؛ وهما اسمان مختلفان بطبيعة الحال. يجب أن توجد الملفات `LanguageBarrier/contrib/lib/xy-vsfilter/VSFilter.lib` و`VSFilter.dll`، إضافة إلى `LanguageBarrier/contrib/include`؛ ولا توجد حاجة لمجلد `contrib/lib/Release`.

## تفعيل الوضع

في ملف patch configuration الخاص بنسخة اللعبة، أضف:

```json
{
  "patch": {
    "rtlDialogue": true,
    "rtlDialogueRightX": 1200,
    "rtlDialogueKeepNameLine": true,
    "rtlDialogueGlyphScaleX": 1.0,
    "rtlDialogueGlyphScaleY": 1.0,
    "rtlDialogueGlyphFitMode": "stretch"
  }
}
```

يجب إبقاء `rtlDialogue` مفعلاً فقط أثناء الاختبار. الكود يقرأ الخيارات عند `gameTextInit()`، ثم يركّب hooks `drawDialogue` و`drawDialogue2` لمسار الحوار العام حتى لو كان `improveDialogueOutlines` غير مفعّل. في النسخة fixed لا يُستخدم `rtlDialogueReverseText` لعكس مصدر glyph؛ كل حرف يُقرأ من الخانة نفسها التي يُرسم داخلها، بينما تُعكس الإحداثيات الأفقية فقط للحوار الحي. هذا يمنع تفاوت الأحجام الناتج عن خلط source glyph بصندوق وجهة مختلف، ولا يغيّر السكربت أو Backlog أو النصوص العامة.

## ترتيب الاختبار

انسخ DLL الناتج إلى مجلد اللعبة وفق طريقة patch الأصلية، واحتفظ بنسخة احتياطية من DLL والملفات الأصلية. لا تختبر فوق ملف الحفظ الوحيد؛ استخدم مشهداً قصيراً يمكن تكراره.

ابدأ بجملة عربية قصيرة من كلمتين أو ثلاث مع `rtlDialogueReverseText` غير مستخدم أو مضبوطًا على `false`. يجب أن يظهر كل glyph من مصدره الأصلي وبحجمه المتسق، بينما يتحول صندوقه أفقيًا داخل سطر الحوار ليبدأ العرض من اليمين ويمتد إلى اليسار. راقب الكتابة التدريجية من اليمين إلى اليسار، ولا تغيّر ترتيب النص في الملفات ولا تفعل reverse خارج DLL أثناء هذا الاختبار.

بعد ذلك اختبر سطراً طويلاً يلتف إلى سطرين. في كل سطر يجب أن يبقى اتجاه الإضافة من اليمين إلى اليسار. راقب الحركة أثناء أول ثواني من ظهور الجملة، لا الإطار النهائي فقط. اختبر أيضاً اسم المتحدث، لأن hook العام قد يشمله إذا كان مخزناً في نفس DialoguePage. ثم اختبر الانتقال إلى الجملة التالية للتأكد من عدم وجود تداخل؛ التعديل الحالي لا يغير Backlog أو mail عمداً.

## قراءة النتيجة

| النتيجة | التفسير المحتمل |
|---|---|
| لا يوجد تغيير إطلاقاً | DLL غير محمّل، أو patch يستخدم configuration آخر، أو signatures لا تطابق executable |
| النص يبدأ يميناً وينتشر يساراً لكن الكلمات متصلة خطأ | اتجاه الإحداثيات يعمل، لكن هناك حاجة إلى shaping؛ هذا ليس عكساً للنص |
| الإطار النهائي صحيح لكن الظهور التدريجي يبدأ من الطرف الخطأ | نحتاج تعديل مصدر العتامة فقط داخل hook الرسم؛ لا نعيد استعمال `renderIndex` لمصدر glyph أو metrics |
| الأحجام متساوية لكن اتصال العربية غير صحيح | اتجاه الرسم يعمل، لكن shaping/contextual forms غير موجودة في أطلس اللعبة؛ هذه مرحلة مستقلة عن RTL |
| السطر الثاني غير صحيح | حدود الأسطر التي تبنيها اللعبة لا تتوافق مع شرط Y الحالي؛ نحتاج تعديل helper ليستخدم معلومات line-break الأصلية |
| crash عند بدء اللعبة | DLL أو configuration غير متوافق، أو signature خاطئة؛ أعد DLL الأصلي وافحص `languagebarrier\log.txt` |

## فحص السجل

بعد التشغيل، راجع:

```text
languagebarrier\log.txt
```

تأكد من ظهور اسم اللعبة واسم patch وعدم وجود فشل في `drawDialogue` أو signature scanning. يجب أن يظهر أيضاً سطر يبدأ بـ `RTL dialogue config:`. قيمة `reverseText` القديمة ليست معيار نجاح في النسخة fixed؛ المعيار هو عدم وجود خلط بين source glyph وdestination box أو تفاوت حجمي ناتج عنه. إذا لم يصل التنفيذ إلى hook، أرسل ملف السجل وملف `gamedef.json` المستخدم، لأن الأرشيف الحالي يحتوي core العام ولا يحتوي signatures الخاصة بإصدار Steins;Gate عند المستخدم.

## حدود النسخة الحالية

هذه النسخة لا تنفذ shaping عربيًا؛ فهي تعزل اتجاه الرسم عن تشكيل الحروف. إذا ظهرت حروف عربية منفصلة أو أشكال ابتدائية/وسطية/نهائية غير صحيحة، فذلك يعني أن مرحلة shaping أو mapping إلى أطلس الخط تحتاج معالجة مستقلة لاحقًا. التعديل الحالي يغيّر مواضع الرسم فقط، ويحافظ على أن يكون source glyph والـmetrics وصندوق الوجهة من الفهرس نفسه، مع إبقاء Backlog والهاتف خارج هذا المسار. بناء DLL فعلي لم يتم داخل بيئة Ubuntu الحالية لغياب MSVC وWindows SDK؛ يجب تنفيذ الأوامر أعلاه على Windows أو عبر بيئة Visual Studio متوافقة.
