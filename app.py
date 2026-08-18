# 1. نعمل مجلد جديد للمشروع ونخشو فيه
mkdir humanos-core
cd humanos-core

# 2. نعمل بيئة افتراضية (عشان الحزم ما تتعارضش مع باقي مشاريعك)
python -m venv venv

# 3. نشغل البيئة الافتراضية (في ويندوز)
venv\Scripts\activate
# (لو كنت في Mac أو Linux، بدل السطر السابق اكتب: source venv/bin/activate)

# 4. نعمل ملفين أساسيين
echo > requirements.txt
echo > .env