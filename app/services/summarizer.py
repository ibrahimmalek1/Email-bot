"""
Extractive text summarization service
Uses sentence scoring based on word frequency and position
"""
import re
from typing import List
from collections import Counter


class Summarizer:
    """Extractive summarizer that extracts key sentences from text"""
    
    # Common stop words to ignore in scoring
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
        'it', 'its', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
        'she', 'we', 'they', 'what', 'which', 'who', 'whom', 'when', 'where',
        'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most',
        'other', 'some', 'such', 'no', 'not', 'only', 'own', 'same', 'so',
        'than', 'too', 'very', 'just', 'also', 'now', 'here', 'there', 'then',
        'if', 'else', 'about', 'into', 'through', 'during', 'before', 'after',
        'above', 'below', 'between', 'under', 'again', 'further', 'once',
        'hi', 'hello', 'dear', 'regards', 'thanks', 'thank', 'sincerely',
        'best', 'cheers', 'sent', 'from', 'subject', 're', 'fwd', 'fw'
    }
    
    def __init__(self, max_sentences: int = 3):
        """
        Initialize summarizer
        
        Args:
            max_sentences: Maximum number of sentences to extract
        """
        self.max_sentences = max_sentences
    
    def _clean_text(self, text: str) -> str:
        """Clean email text by removing signatures, quotes, etc."""
        # Remove email signatures (common patterns)
        text = re.sub(r'--\s*\n.*', '', text, flags=re.DOTALL)
        text = re.sub(r'Sent from my.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Get Outlook for.*', '', text, flags=re.IGNORECASE)
        
        # Remove quoted replies
        text = re.sub(r'^>.*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'On .* wrote:', '', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://\S+', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting on common punctuation
        sentences = re.split(r'(?<=[.!?])\s+', text)
        # Filter out very short sentences
        return [s.strip() for s in sentences if len(s.strip()) > 20]
    
    def _get_word_frequencies(self, text: str) -> Counter:
        """Get word frequencies excluding stop words"""
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        filtered_words = [w for w in words if w not in self.STOP_WORDS]
        return Counter(filtered_words)
    
    def _score_sentence(self, sentence: str, word_freq: Counter, 
                        position: int, total_sentences: int) -> float:
        """
        Score a sentence based on:
        - Word frequency (important words appear more often)
        - Position (first sentences often contain key info)
        - Length (prefer medium-length sentences)
        """
        words = re.findall(r'\b[a-zA-Z]{3,}\b', sentence.lower())
        words = [w for w in words if w not in self.STOP_WORDS]
        
        if not words:
            return 0.0
        
        # Word frequency score
        freq_score = sum(word_freq.get(w, 0) for w in words) / len(words)
        
        # Position score (first and last sentences get bonus)
        position_score = 0.0
        if position < 2:  # First two sentences
            position_score = 1.0
        elif position >= total_sentences - 1:  # Last sentence
            position_score = 0.5
        
        # Length score (prefer 10-30 word sentences)
        word_count = len(words)
        if 10 <= word_count <= 30:
            length_score = 1.0
        elif word_count < 10:
            length_score = word_count / 10
        else:
            length_score = 30 / word_count
        
        # Combined score
        return (freq_score * 0.5) + (position_score * 0.3) + (length_score * 0.2)
    
    def summarize(self, text: str) -> str:
        """
        Extract key sentences from text as a summary
        
        Args:
            text: The email body text to summarize
            
        Returns:
            Extracted summary (top sentences joined)
        """
        if not text or not text.strip():
            return "No content to summarize."
        
        # Clean the text
        cleaned_text = self._clean_text(text)
        
        if len(cleaned_text) < 50:
            return cleaned_text if cleaned_text else "No meaningful content found."
        
        # Split into sentences
        sentences = self._split_sentences(cleaned_text)
        
        if not sentences:
            # If no proper sentences, return first 200 chars
            return cleaned_text[:200] + "..." if len(cleaned_text) > 200 else cleaned_text
        
        if len(sentences) <= self.max_sentences:
            return " ".join(sentences)
        
        # Get word frequencies
        word_freq = self._get_word_frequencies(cleaned_text)
        
        # Score each sentence
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            score = self._score_sentence(sentence, word_freq, i, len(sentences))
            scored_sentences.append((i, sentence, score))
        
        # Sort by score and get top sentences
        scored_sentences.sort(key=lambda x: x[2], reverse=True)
        top_sentences = scored_sentences[:self.max_sentences]
        
        # Sort by original position to maintain flow
        top_sentences.sort(key=lambda x: x[0])
        
        # Join sentences
        summary = " ".join(s[1] for s in top_sentences)
        
        return summary


# Singleton instance
summarizer = Summarizer(max_sentences=3)


def summarize_email(text: str) -> str:
    """Convenience function to summarize email text"""
    return summarizer.summarize(text)
