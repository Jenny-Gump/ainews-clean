# 🚀 External Prompts System

External LLM prompts for easy customization of AI News Parser without code changes.

## 📋 Overview

All LLM prompts are extracted to separate text files for easy editing. The system dynamically loads prompts with variable substitution at runtime.

## 📁 Prompt Files

### 1. `content_cleaner.txt` - DeepSeek Content Cleaning
**Purpose**: Clean raw markdown content from Firecrawl Scrape API

**Key Features**:
- Extracts main article content from raw markdown
- Preserves **real image URLs** (no fake examples!)  
- Adds [IMAGE_N] placeholders for logical image placement
- Removes navigation, social buttons, related articles

**Variables**:
- `{url}` - Article URL for context
- Raw markdown content in user prompt

**Critical Instructions**:
- MUST preserve real image URLs from markdown
- NEVER create fake URLs like "example1.jpg"
- Return JSON with clean content and image array

### 2. `article_translator.txt` - Article Translation (Russian)
**Purpose**: Translate and rewrite articles to Russian with HTML formatting

**Key Features**:
- Expert-level translation with technical awareness  
- HTML formatting (h2, ul, ol, blockquote, strong, em)
- Expert commentary in `<blockquote>` tags
- Category selection from allowed list
- SEO optimization with Yoast fields

**Variables**:
- `{title}` - Article title
- `{url}` - Source URL
- `{published_date}` - Publication date
- `{tags}` - Original tags
- `{categories}` - Original categories  
- `{content}` - Parsed content with [IMAGE_N] placeholders
- `{allowed_categories}` - List of allowed WordPress categories

**Output**: Complete JSON with translated article data

### 3. `tag_generator.txt` - Tag Generation
**Purpose**: Select relevant tags from curated list for WordPress

**Key Features**:
- Selects 2-5 tags from 74 curated tags
- Prioritizes specific AI models/companies over generic terms
- Can create new tags for important AI developments
- Fallback to GPT-3.5 if DeepSeek fails

**Variables**:
- `{title}` - Translated article title
- `{content}` - First 2000 chars of translated content
- `{available_tags}` - JSON array of existing tags

**Output**: JSON array of selected tag names

### 4. `image_metadata.txt` - Image Metadata Translation
**Purpose**: Translate image metadata to Russian for WordPress

**Key Features**:
- Translates alt-text to Russian
- Creates SEO-friendly file slugs
- Handles empty/poor alt-text with article context

**Variables**:
- `{article_title}` - Article title for context
- `{alt_text}` - Original alt-text (may be empty/poor)

**Output**: JSON with Russian alt-text and slug

## 🔧 Usage

### Loading Prompts in Code

```python
from services.prompts_loader import load_prompt

# Load prompt with variables
prompt = load_prompt('content_cleaner', 
    url=article_url,
    content=raw_markdown
)

# Use with LLM API
response = llm_client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_input}
    ]
)
```

### Dynamic Variable Substitution

The `load_prompt()` function automatically substitutes `{variable}` placeholders:

```python
# Prompt file contains: "Process this URL: {url} with content: {content}"
prompt = load_prompt('example', url="https://example.com", content="Hello")
# Result: "Process this URL: https://example.com with content: Hello"
```

## ✏️ Editing Prompts

### Best Practices
1. **Test changes**: Run pipeline after editing prompts
2. **Backup originals**: Keep backups of working prompts  
3. **Gradual changes**: Make small incremental changes
4. **Validate JSON**: Ensure JSON output format remains correct

### Common Variables
- `{url}` - Article source URL
- `{title}` - Article title  
- `{content}` - Article content
- `{published_date}` - Publication date

### Critical Rules
- **NEVER change JSON output format** - will break parsing
- **Test with real data** - not just examples  
- **Keep instructions clear** - AI needs explicit directions
- **Preserve critical instructions** - especially for image URLs

## 🧪 Testing Prompts

### Test with Single Pipeline
```bash
cd "/Users/skynet/Desktop/AI DEV/ainews-clean"
source venv/bin/activate

# Process one article to test all prompts
python core/main.py --single-pipeline
```

### Check Results
1. **Content Cleaning**: Verify real image URLs (not "example.jpg")
2. **Translation**: Check HTML formatting and Russian quality
3. **Tags**: Ensure tags appear in WordPress (check REST API)
4. **Images**: Verify alt-text is in Russian

## 🚨 Troubleshooting

### Common Issues

#### 1. JSON Parsing Errors
**Problem**: LLM returns invalid JSON
**Solution**: Review JSON format in prompt, add explicit examples

#### 2. Fake Image URLs  
**Problem**: DeepSeek creates "example.jpg" URLs
**Solution**: Strengthen instructions in `content_cleaner.txt` about real URLs

#### 3. Missing Tags
**Problem**: Tags not appearing in WordPress
**Solution**: Check `tag_generator.txt` JSON format and variable names

#### 4. Poor Translation Quality
**Problem**: Translation lacks expertise or context  
**Solution**: Enhance personality/expertise instructions in `article_translator.txt`

### Debug Steps
1. Check logs for LLM API errors
2. Verify prompt variable substitution  
3. Test with simple article first
4. Compare output JSON with expected format

## 📚 Technical Details

### Prompt Loader Implementation
- Located in `services/prompts_loader.py`
- Caches loaded prompts for performance
- Handles file reading errors gracefully
- Supports nested variable substitution

### Integration Points
- **Phase 2**: `content_cleaner.txt` → content_parser.py
- **Phase 4**: `article_translator.txt` → wordpress_publisher.py  
- **Phase 4**: `tag_generator.txt` → single_pipeline.py
- **Phase 5**: `image_metadata.txt` → wordpress_publisher.py

### Error Handling
- Fallback to hardcoded prompts if files missing
- Graceful degradation with logging
- Retry mechanisms for LLM API calls

## 📊 Version History

### v2.1 (August 7, 2025) - Initial External Prompts
- ✅ Extracted all 4 prompts from hardcoded strings
- ✅ Implemented dynamic variable substitution  
- ✅ Fixed image URL preservation
- ✅ Fixed tag generation with proper logging
- ✅ Added comprehensive error handling

---

**Last Updated**: August 7, 2025 | **System Version**: 2.1