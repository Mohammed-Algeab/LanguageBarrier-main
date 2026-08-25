# إصلاح أخطاء بناء LanguageBarrier v14

## المشكلة الأولى: macro الحوار

داخل `DEF_DRAW_DIALOGUE_HOOK` كانت هناك ثلاثة أسطر تعليق تبدأ بـ`//`، مع أن تعريف macro يستخدم `\\` لاستمرار السطر. في الـpreprocessor، علامة `\\` تُزيل نهاية السطر أولًا، لذلك يتحول التعليق `//` إلى تعليق يمتد عبر بقية macro، وقد يختفي جزء من جسم الدالة ويظهر خطأ مضلل مثل:

```text
C2601: local function definitions are illegal
C1075: '{': no matching token found
```

الإصلاح هو تحويل التعليق إلى تعليق كتلي `/* ... */` مع استمرار السطر. القوس `}` في نهاية macro موجود أصلًا، ولا ينبغي إضافة قوس آخر.

## المشكلة الثانية: forceLTR

`replaceTextFragment` يستقبل كائن `LazyAllocatingProcessedString`. العضو `result` داخل هذا الصنف خاص `private`، كما أن الصنف نفسه لا يملك عضوًا اسمه `forceLTR`. لذلك فالتغيير المباشر إلى `result.result.forceLTR` ليس إصلاحًا كاملًا، لأنه سيؤدي إلى خطأ وصول إلى عضو خاص.

الإصلاح الصحيح هو إضافة دالة عامة صغيرة:

```cpp
void markForceLTR() { result.forceLTR = true; }
```

ثم استدعاؤها من `replaceTextFragment`:

```cpp
result.markForceLTR();
```

تم تطبيق الإصلاحين في هذه الحزمة. لا يمكن إجراء بناء MSVC داخل بيئة Linux الحالية؛ يجب تشغيل GitHub Actions أو Visual Studio للتأكد النهائي من بناء DLL على Windows/x86.
