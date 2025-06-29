"""
Content Quality Assessment and Enhancement
Quality metrics and content improvement algorithms
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from collections import Counter
import statistics

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """Comprehensive quality metrics for content"""
    readability_score: float
    information_density: float
    coherence_score: float
    completeness_score: float
    factual_accuracy: float
    linguistic_quality: float
    overall_score: float
    metadata: Dict[str, Any]


class ContentQualityAssessor:
    """Assess content quality using multiple metrics"""
    
    def __init__(self):
        # Common words for readability analysis
        self.common_words = {
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have',
            'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do',
            'at', 'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say',
            'her', 'she', 'or', 'an', 'will', 'my', 'one', 'all', 'would',
            'there', 'their'
        }
        
    def assess_quality(self, content: str, context: Dict[str, Any] = None) -> QualityMetrics:
        """Perform comprehensive quality assessment"""
        if not content or not content.strip():
            return QualityMetrics(
                readability_score=0.0,
                information_density=0.0,
                coherence_score=0.0,
                completeness_score=0.0,
                factual_accuracy=0.0,
                linguistic_quality=0.0,
                overall_score=0.0,
                metadata={"error": "empty_content"}
            )
        
        # Calculate individual metrics
        readability = self._assess_readability(content)
        info_density = self._assess_information_density(content)
        coherence = self._assess_coherence(content)
        completeness = self._assess_completeness(content, context)
        factual_accuracy = self._assess_factual_accuracy(content)
        linguistic_quality = self._assess_linguistic_quality(content)
        
        # Calculate overall score (weighted average)
        weights = {
            'readability': 0.15,
            'information_density': 0.20,
            'coherence': 0.20,
            'completeness': 0.15,
            'factual_accuracy': 0.15,
            'linguistic_quality': 0.15
        }
        
        overall = (
            readability * weights['readability'] +
            info_density * weights['information_density'] +
            coherence * weights['coherence'] +
            completeness * weights['completeness'] +
            factual_accuracy * weights['factual_accuracy'] +
            linguistic_quality * weights['linguistic_quality']
        )
        
        return QualityMetrics(
            readability_score=readability,
            information_density=info_density,
            coherence_score=coherence,
            completeness_score=completeness,
            factual_accuracy=factual_accuracy,
            linguistic_quality=linguistic_quality,
            overall_score=overall,
            metadata={
                "content_length": len(content),
                "word_count": len(re.findall(r'\b\w+\b', content)),
                "sentence_count": len(re.split(r'[.!?]+', content)) - 1,
                "weights": weights
            }
        )
    
    def _assess_readability(self, content: str) -> float:
        """Assess readability using simplified metrics"""
        sentences = [s.strip() for s in re.split(r'[.!?]+', content) if s.strip()]
        words = re.findall(r'\b\w+\b', content.lower())
        
        if not sentences or not words:
            return 0.0
        
        # Average sentence length
        avg_sentence_length = len(words) / len(sentences)
        
        # Syllable estimation (simplified)
        total_syllables = sum(self._estimate_syllables(word) for word in words)
        avg_syllables_per_word = total_syllables / len(words) if words else 0
        
        # Common word ratio
        common_word_count = sum(1 for word in words if word in self.common_words)
        common_word_ratio = common_word_count / len(words) if words else 0
        
        # Readability score (0-1, higher is more readable)
        # Optimal ranges: 15-20 words/sentence, 1.5-2 syllables/word, 60%+ common words
        length_score = max(0, 1 - abs(avg_sentence_length - 17.5) / 17.5)
        syllable_score = max(0, 1 - abs(avg_syllables_per_word - 1.75) / 1.75)
        common_score = min(common_word_ratio / 0.6, 1.0)
        
        readability = (length_score + syllable_score + common_score) / 3
        return min(max(readability, 0.0), 1.0)
    
    def _assess_information_density(self, content: str) -> float:
        """Assess information density and uniqueness"""
        words = re.findall(r'\b\w+\b', content.lower())
        
        if not words:
            return 0.0
        
        # Vocabulary richness (unique words / total words)
        unique_words = set(words)
        vocab_richness = len(unique_words) / len(words)
        
        # Information content indicators
        info_indicators = [
            'data', 'information', 'fact', 'study', 'research', 'analysis',
            'result', 'finding', 'evidence', 'statistic', 'number', 'percent',
            'according', 'report', 'survey', 'experiment', 'conclusion'
        ]
        
        info_word_count = sum(1 for word in words if word in info_indicators)
        info_word_ratio = info_word_count / len(words) if words else 0
        
        # Repetition penalty
        word_counts = Counter(words)
        max_repetition = max(word_counts.values()) if word_counts else 1
        repetition_penalty = 1 / max_repetition if max_repetition > 1 else 1
        
        # Combine metrics
        density_score = (vocab_richness * 0.5 + info_word_ratio * 0.3 + repetition_penalty * 0.2)
        return min(max(density_score, 0.0), 1.0)
    
    def _assess_coherence(self, content: str) -> float:
        """Assess logical flow and coherence"""
        sentences = [s.strip() for s in re.split(r'[.!?]+', content) if s.strip()]
        
        if len(sentences) < 2:
            return 1.0 if sentences else 0.0
        
        # Transition words and phrases
        transitions = [
            'however', 'therefore', 'moreover', 'furthermore', 'additionally',
            'consequently', 'meanwhile', 'nevertheless', 'similarly', 'likewise',
            'in contrast', 'on the other hand', 'as a result', 'for example',
            'in addition', 'first', 'second', 'third', 'finally', 'next'
        ]
        
        # Count transitions
        transition_count = 0
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(trans in sentence_lower for trans in transitions):
                transition_count += 1
        
        transition_ratio = transition_count / len(sentences) if sentences else 0
        
        # Topic consistency (simplified by word overlap between sentences)
        consistency_scores = []
        for i in range(len(sentences) - 1):
            words1 = set(re.findall(r'\b\w+\b', sentences[i].lower()))
            words2 = set(re.findall(r'\b\w+\b', sentences[i + 1].lower()))
            
            if words1 and words2:
                overlap = len(words1.intersection(words2))
                union = len(words1.union(words2))
                consistency = overlap / union if union > 0 else 0
                consistency_scores.append(consistency)
        
        avg_consistency = statistics.mean(consistency_scores) if consistency_scores else 0
        
        # Combine coherence indicators
        coherence_score = (transition_ratio * 0.4 + avg_consistency * 0.6)
        return min(max(coherence_score, 0.0), 1.0)
    
    def _assess_completeness(self, content: str, context: Dict[str, Any] = None) -> float:
        """Assess content completeness"""
        # Basic completeness indicators
        words = re.findall(r'\b\w+\b', content.lower())
        sentences = [s.strip() for s in re.split(r'[.!?]+', content) if s.strip()]
        
        if not words or not sentences:
            return 0.0
        
        # Length adequacy (content should be substantial)
        length_score = min(len(words) / 100, 1.0)  # 100+ words is good
        
        # Structural completeness
        has_introduction = any(word in words[:50] for word in ['introduction', 'overview', 'summary'])
        has_conclusion = any(word in words[-50:] for word in ['conclusion', 'summary', 'finally'])
        
        structure_score = (0.5 if has_introduction else 0) + (0.5 if has_conclusion else 0)
        
        # Context-specific completeness
        context_score = 0.5  # Default
        if context and 'required_topics' in context:
            required_topics = context['required_topics']
            covered_topics = sum(1 for topic in required_topics if topic.lower() in content.lower())
            context_score = covered_topics / len(required_topics) if required_topics else 1.0
        
        # Combine completeness metrics
        completeness = (length_score * 0.4 + structure_score * 0.3 + context_score * 0.3)
        return min(max(completeness, 0.0), 1.0)
    
    def _assess_factual_accuracy(self, content: str) -> float:
        """Assess factual accuracy indicators (simplified)"""
        # Look for uncertainty and factual indicators
        uncertainty_words = ['maybe', 'perhaps', 'possibly', 'might', 'could', 'allegedly']
        factual_words = ['study', 'research', 'data', 'evidence', 'fact', 'proven', 'verified']
        
        words = re.findall(r'\b\w+\b', content.lower())
        
        if not words:
            return 0.0
        
        uncertainty_count = sum(1 for word in words if word in uncertainty_words)
        factual_count = sum(1 for word in words if word in factual_words)
        
        # High factual indicators and low uncertainty = higher accuracy score
        factual_ratio = factual_count / len(words) if words else 0
        uncertainty_penalty = uncertainty_count / len(words) if words else 0
        
        accuracy_score = min(factual_ratio * 10, 1.0) - min(uncertainty_penalty * 5, 0.5)
        return min(max(accuracy_score, 0.0), 1.0)
    
    def _assess_linguistic_quality(self, content: str) -> float:
        """Assess grammar and linguistic quality"""
        # Simple linguistic quality indicators
        
        # Check for proper capitalization
        sentences = [s.strip() for s in re.split(r'[.!?]+', content) if s.strip()]
        properly_capitalized = sum(1 for s in sentences if s and s[0].isupper())
        capitalization_score = properly_capitalized / len(sentences) if sentences else 0
        
        # Check for punctuation
        punctuation_count = len(re.findall(r'[.!?,:;]', content))
        words = re.findall(r'\b\w+\b', content)
        punctuation_ratio = punctuation_count / len(words) if words else 0
        punctuation_score = min(punctuation_ratio / 0.1, 1.0)  # ~10% punctuation is good
        
        # Check for spelling (very basic - look for common errors)
        spelling_errors = [
            'teh', 'recieve', 'seperate', 'occured', 'definately',
            'priviledge', 'neccessary', 'begining', 'beleive', 'acheive'
        ]
        error_count = sum(1 for word in words if word.lower() in spelling_errors)
        spelling_score = max(1 - error_count / len(words) * 10, 0) if words else 1
        
        # Combine linguistic quality metrics
        linguistic_quality = (capitalization_score * 0.3 + punctuation_score * 0.4 + spelling_score * 0.3)
        return min(max(linguistic_quality, 0.0), 1.0)
    
    def _estimate_syllables(self, word: str) -> int:
        """Estimate syllable count for a word"""
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        prev_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                syllable_count += 1
            prev_was_vowel = is_vowel
        
        # Handle silent e
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1
        
        return max(syllable_count, 1)


class ContentEnhancer:
    """Enhance content quality through automated improvements"""
    
    def __init__(self):
        self.enhancement_rules = self._build_enhancement_rules()
    
    def enhance(self, content: str, quality_metrics: QualityMetrics = None) -> Tuple[str, Dict[str, Any]]:
        """Enhance content based on quality assessment"""
        if not content:
            return content, {"error": "empty_content"}
        
        enhanced_content = content
        applied_enhancements = []
        
        # Apply enhancement rules
        for rule in self.enhancement_rules:
            if rule['condition'](enhanced_content, quality_metrics):
                enhanced_content = rule['enhance'](enhanced_content)
                applied_enhancements.append(rule['name'])
        
        enhancement_summary = {
            "original_length": len(content),
            "enhanced_length": len(enhanced_content),
            "applied_enhancements": applied_enhancements,
            "improvement_count": len(applied_enhancements)
        }
        
        return enhanced_content, enhancement_summary
    
    def _build_enhancement_rules(self) -> List[Dict]:
        """Build enhancement rules"""
        return [
            {
                'name': 'fix_capitalization',
                'condition': lambda content, metrics: self._needs_capitalization_fix(content),
                'enhance': self._fix_capitalization
            },
            {
                'name': 'improve_punctuation',
                'condition': lambda content, metrics: self._needs_punctuation_improvement(content),
                'enhance': self._improve_punctuation
            },
            {
                'name': 'add_transitions',
                'condition': lambda content, metrics: metrics and metrics.coherence_score < 0.5,
                'enhance': self._add_transitions
            },
            {
                'name': 'remove_redundancy',
                'condition': lambda content, metrics: self._has_redundancy(content),
                'enhance': self._remove_redundancy
            },
            {
                'name': 'improve_structure',
                'condition': lambda content, metrics: metrics and metrics.completeness_score < 0.6,
                'enhance': self._improve_structure
            }
        ]
    
    def _needs_capitalization_fix(self, content: str) -> bool:
        """Check if content needs capitalization fixes"""
        sentences = [s.strip() for s in re.split(r'[.!?]+', content) if s.strip()]
        if not sentences:
            return False
        
        uncapitalized = sum(1 for s in sentences if s and not s[0].isupper())
        return uncapitalized / len(sentences) > 0.2
    
    def _fix_capitalization(self, content: str) -> str:
        """Fix capitalization issues"""
        # Capitalize sentence beginnings
        sentences = re.split(r'([.!?]+)', content)
        fixed_sentences = []
        
        for i, part in enumerate(sentences):
            if i % 2 == 0 and part.strip():  # Text parts (not punctuation)
                part = part.strip()
                if part and part[0].islower():
                    part = part[0].upper() + part[1:]
                fixed_sentences.append(part)
            else:
                fixed_sentences.append(part)
        
        return ''.join(fixed_sentences)
    
    def _needs_punctuation_improvement(self, content: str) -> bool:
        """Check if content needs punctuation improvement"""
        words = re.findall(r'\b\w+\b', content)
        punctuation = re.findall(r'[.!?,;:]', content)
        
        if not words:
            return False
        
        punct_ratio = len(punctuation) / len(words)
        return punct_ratio < 0.05  # Less than 5% punctuation
    
    def _improve_punctuation(self, content: str) -> str:
        """Add missing punctuation"""
        # Add periods to sentences that don't end with punctuation
        sentences = content.split('\n')
        improved_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and not re.search(r'[.!?]$', sentence):
                sentence += '.'
            improved_sentences.append(sentence)
        
        return '\n'.join(improved_sentences)
    
    def _add_transitions(self, content: str) -> str:
        """Add transition words to improve coherence"""
        sentences = [s.strip() for s in re.split(r'[.!?]+', content) if s.strip()]
        
        if len(sentences) < 2:
            return content
        
        transitions = ['Furthermore', 'Additionally', 'Moreover', 'However', 'Therefore']
        
        # Add transitions to some sentences (every 3rd sentence)
        for i in range(2, len(sentences), 3):
            if not any(trans.lower() in sentences[i].lower() for trans in transitions):
                transition = transitions[i % len(transitions)]
                sentences[i] = f"{transition}, {sentences[i].lower()}"
        
        return '. '.join(sentences) + '.'
    
    def _has_redundancy(self, content: str) -> bool:
        """Check for redundant content"""
        sentences = [s.strip() for s in re.split(r'[.!?]+', content) if s.strip()]
        
        if len(sentences) < 3:
            return False
        
        # Look for very similar sentences
        for i in range(len(sentences) - 1):
            words1 = set(re.findall(r'\b\w+\b', sentences[i].lower()))
            words2 = set(re.findall(r'\b\w+\b', sentences[i + 1].lower()))
            
            if words1 and words2:
                overlap = len(words1.intersection(words2))
                similarity = overlap / max(len(words1), len(words2))
                if similarity > 0.8:  # Very similar sentences
                    return True
        
        return False
    
    def _remove_redundancy(self, content: str) -> str:
        """Remove redundant sentences"""
        sentences = [s.strip() for s in re.split(r'[.!?]+', content) if s.strip()]
        
        if len(sentences) < 2:
            return content
        
        filtered_sentences = [sentences[0]]  # Keep first sentence
        
        for i in range(1, len(sentences)):
            current_words = set(re.findall(r'\b\w+\b', sentences[i].lower()))
            is_redundant = False
            
            for prev_sentence in filtered_sentences:
                prev_words = set(re.findall(r'\b\w+\b', prev_sentence.lower()))
                
                if current_words and prev_words:
                    overlap = len(current_words.intersection(prev_words))
                    similarity = overlap / max(len(current_words), len(prev_words))
                    
                    if similarity > 0.8:  # Too similar
                        is_redundant = True
                        break
            
            if not is_redundant:
                filtered_sentences.append(sentences[i])
        
        return '. '.join(filtered_sentences) + '.'
    
    def _improve_structure(self, content: str) -> str:
        """Improve content structure"""
        sentences = [s.strip() for s in re.split(r'[.!?]+', content) if s.strip()]
        
        if len(sentences) < 3:
            return content
        
        # Add simple structure cues
        structured_content = f"Overview: {sentences[0]}.\n\n"
        
        # Add body content
        if len(sentences) > 2:
            body_sentences = sentences[1:-1]
            structured_content += "Details: " + '. '.join(body_sentences) + ".\n\n"
        
        # Add conclusion
        structured_content += f"Summary: {sentences[-1]}."
        
        return structured_content


# Usage example
if __name__ == "__main__":
    sample_content = """
    artificial intelligence is transforming many industries. machine learning algorithms 
    are being used everywhere. companies are investing heavily in AI technology. 
    the future looks bright for AI development. many experts believe AI will continue growing.
    """
    
    # Assess quality
    assessor = ContentQualityAssessor()
    quality = assessor.assess_quality(sample_content)
    
    print("Quality Assessment:")
    print(f"Overall Score: {quality.overall_score:.2f}")
    print(f"Readability: {quality.readability_score:.2f}")
    print(f"Information Density: {quality.information_density:.2f}")
    print(f"Coherence: {quality.coherence_score:.2f}")
    print(f"Completeness: {quality.completeness_score:.2f}")
    
    # Enhance content
    enhancer = ContentEnhancer()
    enhanced_content, summary = enhancer.enhance(sample_content, quality)
    
    print("\nEnhancement Summary:")
    print(f"Applied enhancements: {summary['applied_enhancements']}")
    print(f"Enhanced content:\n{enhanced_content}")
