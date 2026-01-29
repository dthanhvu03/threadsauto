# Cursor Rules - Threads Automation Tool

> **Tổng hợp các rules và guidelines cho Threads Automation Tool**  
> Tất cả files trong thư mục này được apply tự động khi làm việc với project

---

## 📋 Tổng Quan

Thư mục `.cursor/rules/` chứa các file rules (`.mdc`) được Cursor tự động apply. Mỗi file có vai trò riêng và liên kết với nhau để tạo một hệ thống guidelines hoàn chỉnh.

---

## 📁 Cấu Trúc Files

### 1. **prompt.mdc** - Core Requirements
**Vai trò:** Định nghĩa requirements, objectives, và functional specifications

**Nội dung:**
- ROLE definition (Senior Automation Engineer)
- OBJECTIVE (build local Threads automation tool)
- STRICT CONSTRAINTS (mandatory rules)
- LOGIN STRATEGY (session reuse)
- FUNCTIONAL REQUIREMENTS (12 sections)
- SUCCESS CRITERIA

**Liên kết:**
- → `rulesthreads.mdc`: Skills cần thiết để implement
- → `dev.mdc`: Development workflow để implement
- → `qc.mdc`: Testing criteria để validate
- → `code_standards.mdc`: Coding standards để follow

**Khi nào dùng:**
- Khi bắt đầu project mới
- Khi cần hiểu requirements
- Khi review implementation

---

### 2. **rulesthreads.mdc** - Skills & Mindset
**Vai trò:** Framework tư duy và kỹ năng của kỹ sư automation

**Nội dung:**
- Foundation Mindset (Automation ≠ Spam, Platform-first, Fail-safe)
- Tech Stack & Core Skills (Browser Automation, Anti-detection, UI Understanding)
- System Design (Account Management, Safety Guard, Logging)
- Reverse Thinking (Platform Defense)
- Maintainability & Evolution

**Liên kết:**
- ← `prompt.mdc`: Requirements cần implement
- → `dev.mdc`: Best practices để apply skills
- → `code_standards.mdc`: Standards để code đúng cách

**Khi nào dùng:**
- Khi cần hiểu mindset và approach
- Khi design architecture
- Khi review code quality

---

### 3. **dev.mdc** - Development Guidelines
**Vai trò:** Development workflow, best practices, và common patterns

**Nội dung:**
- Development Workflow (setup, process, git)
- Coding Standards (PEP 8, organization)
- Best Practices (anti-detection, UI handling, selectors)
- Common Patterns (browser automation, retry, state machine)
- Debugging Tips
- Performance Optimization
- Security Best Practices

**Liên kết:**
- ← `prompt.mdc`: Requirements để implement
- ← `rulesthreads.mdc`: Skills để apply
- → `code_standards.mdc`: Detailed coding standards
- → `qc.mdc`: Testing approach

**Khi nào dùng:**
- Khi setup development environment
- Khi implement features
- Khi debug issues
- Khi optimize performance

---

### 4. **qc.mdc** - Quality Control & Testing
**Vai trò:** Testing strategy, code quality standards, và review criteria

**Nội dung:**
- Testing Strategy (unit, integration, E2E, manual)
- Code Quality Standards
- Review Checklist
- Validation Criteria (functional, safety, anti-detection, UI)
- Testing Tools & Frameworks
- Production Readiness Checklist

**Liên kết:**
- ← `prompt.mdc`: Success criteria để validate
- ← `dev.mdc`: Code để test
- ← `code_standards.mdc`: Standards để review

**Khi nào dùng:**
- Khi viết tests
- Khi review code
- Khi validate implementation
- Trước khi deploy

---

### 5. **code_standards.mdc** - Code Standards & Conventions
**Vai trò:** Detailed coding standards, style guide, và conventions

**Nội dung:**
- Code Style (PEP 8)
- Naming Conventions
- Code Structure
- Documentation Standards
- Type Hints
- Error Handling Conventions
- Logging Conventions
- Testing Conventions
- Import Conventions
- Code Organization
- Forbidden Patterns

**Liên kết:**
- ← `dev.mdc`: General guidelines
- → `qc.mdc`: Standards để review

**Khi nào dùng:**
- Khi viết code
- Khi review code style
- Khi enforce conventions
- Khi setup linters

---

## 🔗 Mối Quan Hệ Giữa Các Files

```
┌─────────────────┐
│  prompt.mdc    │  Core Requirements
│  (Foundation)  │
└────────┬───────┘
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
┌─────────────────┐  ┌─────────────────┐
│ rulesthreads.mdc│  │    dev.mdc      │
│  (Mindset)      │  │  (Workflow)     │
└────────┬───────┘  └────────┬────────┘
         │                    │
         │                    │
         └──────────┬─────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  code_standards.mdc  │
         │   (Standards)        │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │      qc.mdc          │
         │   (Testing & QC)      │
         └──────────────────────┘
```

### Flow:

1. **prompt.mdc** → Define WHAT to build (requirements)
2. **rulesthreads.mdc** → Define HOW to think (mindset & skills)
3. **dev.mdc** → Define HOW to work (workflow & practices)
4. **code_standards.mdc** → Define HOW to code (standards)
5. **qc.mdc** → Define HOW to validate (testing & review)

---

## 🎯 Sử Dụng Theo Ngữ Cảnh

### Khi Bắt Đầu Project:
1. Đọc `prompt.mdc` - Hiểu requirements
2. Đọc `rulesthreads.mdc` - Hiểu mindset
3. Đọc `dev.mdc` - Setup environment

### Khi Implement Feature:
1. Tham khảo `prompt.mdc` - Requirements
2. Follow `dev.mdc` - Workflow & patterns
3. Apply `code_standards.mdc` - Coding standards
4. Check `rulesthreads.mdc` - Best practices

### Khi Review Code:
1. Check `code_standards.mdc` - Style & conventions
2. Check `dev.mdc` - Best practices
3. Check `qc.mdc` - Review checklist
4. Validate `prompt.mdc` - Requirements met

### Khi Test:
1. Follow `qc.mdc` - Testing strategy
2. Check `prompt.mdc` - Success criteria
3. Apply `code_standards.mdc` - Testing conventions

---

## 📊 Coverage Matrix

| Aspect | prompt.mdc | rulesthreads.mdc | dev.mdc | code_standards.mdc | qc.mdc |
|--------|------------|------------------|---------|---------------------|--------|
| **Requirements** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Mindset** | ⚠️ | ✅ | ⚠️ | ❌ | ❌ |
| **Workflow** | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Best Practices** | ⚠️ | ✅ | ✅ | ❌ | ⚠️ |
| **Coding Standards** | ❌ | ❌ | ⚠️ | ✅ | ⚠️ |
| **Testing** | ❌ | ❌ | ⚠️ | ⚠️ | ✅ |
| **Review** | ❌ | ❌ | ❌ | ⚠️ | ✅ |

**Legend:**
- ✅ Primary focus
- ⚠️ Secondary mention
- ❌ Not covered

---

## 🔍 Quick Reference

### Tìm Thông Tin Về:

**Requirements & Objectives:**
→ `prompt.mdc`

**Mindset & Approach:**
→ `rulesthreads.mdc`

**Setup & Workflow:**
→ `dev.mdc` (Section I, II)

**Coding Patterns:**
→ `dev.mdc` (Section IV)

**Code Style:**
→ `code_standards.mdc` (Section I, II, III)

**Type Hints:**
→ `code_standards.mdc` (Section V)

**Error Handling:**
→ `code_standards.mdc` (Section VI)
→ `dev.mdc` (Section II.3)

**Logging:**
→ `code_standards.mdc` (Section VII)
→ `dev.mdc` (Section II.4)

**Testing:**
→ `qc.mdc` (Section I, V)
→ `code_standards.mdc` (Section VIII)

**Review Checklist:**
→ `qc.mdc` (Section III, VII)
→ `code_standards.mdc` (Section XII)

**Anti-detection:**
→ `dev.mdc` (Section III.1)
→ `prompt.mdc` (Section 3)

**UI State Handling:**
→ `dev.mdc` (Section III.2)
→ `prompt.mdc` (Section 3)

**Safety Guard:**
→ `prompt.mdc` (Section 6)
→ `qc.mdc` (Section IV.2)

---

## 📝 Notes

### File Format:
- Tất cả files có `alwaysApply: true` → Tự động apply
- Format: Markdown với frontmatter
- Encoding: UTF-8

### Updates:
- Khi update requirements → Update `prompt.mdc`
- Khi update standards → Update `code_standards.mdc`
- Khi update workflow → Update `dev.mdc`
- Khi update testing → Update `qc.mdc`

### Consistency:
- Tất cả files phải consistent với nhau
- Cross-reference giữa các files
- No contradictions

---

## 🚀 Getting Started

1. **New Developer:**
   - Start with `prompt.mdc` (understand requirements)
   - Read `rulesthreads.mdc` (understand mindset)
   - Follow `dev.mdc` (setup environment)
   - Apply `code_standards.mdc` (write code)

2. **Implementing Feature:**
   - Check `prompt.mdc` (requirements)
   - Follow `dev.mdc` (workflow)
   - Apply `code_standards.mdc` (standards)
   - Test with `qc.mdc` (validation)

3. **Code Review:**
   - Check `code_standards.mdc` (style)
   - Check `dev.mdc` (best practices)
   - Check `qc.mdc` (review checklist)

---

**Last Updated:** 2024  
**Version:** 1.0.0  
**Maintainer:** Engineering Team

