import { describe, it, expect } from 'vitest';
import { Citation } from '../types';

describe('Citation logic and formatting', () => {
  it('correctly handles single page range vs multi-page range', () => {
    const singlePage: Citation = {
      document_id: '123e4567-e89b-12d3-a456-426614174000',
      document_name: 'test.pdf',
      page_start: 3,
      page_end: 3,
      text: 'Test citation excerpt',
      similarity_score: 0.884,
    };

    const multiPage: Citation = {
      document_id: '123e4567-e89b-12d3-a456-426614174000',
      document_name: 'test.pdf',
      page_start: 2,
      page_end: 4,
      text: 'Multi-page excerpt',
      similarity_score: 0.75,
    };

    const formatPageLabel = (c: Citation) =>
      c.page_start === c.page_end ? `Page ${c.page_start}` : `Pages ${c.page_start}–${c.page_end}`;

    expect(formatPageLabel(singlePage)).toBe('Page 3');
    expect(formatPageLabel(multiPage)).toBe('Pages 2–4');
    expect(Math.round(singlePage.similarity_score * 100)).toBe(88);
    expect(Math.round(multiPage.similarity_score * 100)).toBe(75);
  });
});
