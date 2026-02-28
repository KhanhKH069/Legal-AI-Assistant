# HR Q&A Knowledge Base - 150 Questions

## 📋 Structure

1. **01_HR_Policies.md** - 30 questions
   - Working hours, dress code, attendance
   - Code of conduct, communication
   - Performance, development, workplace

2. **02_Leave_Policies.md** - 20 questions
   - Annual leave, sick leave
   - Special leave (marriage, bereavement, maternity)
   - Unpaid leave, public holidays

3. **03_Compensation.md** - 25 questions
   - Salary structure, bonuses
   - Allowances, insurance
   - Retirement, incentives

4. **04_Onboarding.md** - 25 questions  
   - First day/week procedures
   - Training & orientation
   - Probation process

5. **05_Benefits.md** - 20 questions
   - Health & wellness
   - Work-life balance
   - Professional development

6. **06_Compliance.md** - 30 questions
   - Labor law
   - Data protection
   - Corporate governance

## 🎯 Usage

### For Vector Database:
```bash
python index_to_chromadb.py
```

This will:
1. Read all .md files
2. Extract Q&A pairs
3. Generate embeddings
4. Store in ChromaDB

### Query Example:
```python
# User asks: "Công ty cho nghỉ mấy ngày?"
# → Vector search finds Q1 in Leave Policies
# → Returns: "12 ngày/năm cho full-time"
```

## ✨ Features

- **Semantic matching**: Different wording, same answer
- **Variations**: Multiple ways to ask same question
- **Structured**: Consistent format
- **Vietnamese**: Native language support
- **Metadata**: Category, tags, last updated

## 📊 Coverage

- ✅ 150 core HR questions
- ✅ ~500 question variations
- ✅ Comprehensive answers
- ✅ Company policies
- ✅ Legal compliance

## 🔄 Maintenance

Update questions:
1. Edit .md files
2. Run: `python index_to_chromadb.py --reindex`
3. Done!

