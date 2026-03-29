import React, { useState } from 'react';
import './HomePage.css';

/* ---------- Mock data ---------- */
const MOCK_PAPERS = [
  {
    id: 1,
    title: 'Attention Is All You Need',
    authors: 'Vaswani, A. et al.',
    abstract:
      'We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on machine translation tasks show these models achieve superior quality.',
    citations: 98432,
    year: 2017,
    relevance: 97,
  },
  {
    id: 2,
    title: 'BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding',
    authors: 'Devlin, J., Chang, M., Lee, K., Toutanova, K.',
    abstract:
      'We introduce a new language representation model called BERT, designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers.',
    citations: 72156,
    year: 2019,
    relevance: 94,
  },
  {
    id: 3,
    title: 'Language Models are Few-Shot Learners',
    authors: 'Brown, T. et al.',
    abstract:
      'We demonstrate that scaling up language models greatly improves task-agnostic, few-shot performance, sometimes even reaching competitiveness with prior state-of-the-art fine-tuning approaches.',
    citations: 31245,
    year: 2020,
    relevance: 91,
  },
  {
    id: 4,
    title: 'Deep Residual Learning for Image Recognition',
    authors: 'He, K., Zhang, X., Ren, S., Sun, J.',
    abstract:
      'We present a residual learning framework to ease the training of networks that are substantially deeper than those used previously. We explicitly reformulate the layers as learning residual functions.',
    citations: 145678,
    year: 2016,
    relevance: 85,
  },
  {
    id: 5,
    title: 'Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks',
    authors: 'Lewis, P. et al.',
    abstract:
      'We explore a general-purpose fine-tuning recipe for retrieval-augmented generation (RAG) — models which combine pre-trained parametric and non-parametric memory for language generation.',
    citations: 4523,
    year: 2020,
    relevance: 88,
  },
];


/* ---------- Component ---------- */
const HomePage: React.FC = () => {
  /* Search state */
  const [searchQuery, setSearchQuery] = useState('');
  const [keywords, setKeywords] = useState<string[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [yearFilter, setYearFilter] = useState('all');
  const [sortBy, setSortBy] = useState('relevance');



  /* ----- Handlers ----- */
  const handleSearch = () => {
    const trimmed = searchQuery.trim();
    if (!trimmed) return;
    if (!keywords.includes(trimmed)) {
      setKeywords((prev) => [...prev, trimmed]);
    }
    setSearchQuery('');
    setHasSearched(true);
  };

  const handleSearchKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSearch();
    }
  };

  const removeKeyword = (kw: string) => {
    setKeywords((prev) => prev.filter((k) => k !== kw));
  };



  const formatNumber = (n: number) =>
    n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n);

  /* ----- Render ----- */
  return (
    <div className="home-page">
      {/* ===== SEARCH PANEL ===== */}
      <aside className="glass-panel search-panel" id="search-panel">
        <div className="panel-header">
          <h2>
            <span className="icon">🔍</span> Discover Papers
          </h2>
          <p>Enter keywords to find relevant research</p>
        </div>

        <div className="panel-body">
          <div className="search-input-group">
            <input
              id="search-input"
              className="search-input"
              type="text"
              placeholder="e.g. transformer, attention mechanism…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={handleSearchKeyDown}
            />
            <button id="search-btn" className="search-btn" onClick={handleSearch}>
              Search
            </button>
          </div>

          {keywords.length > 0 && (
            <div className="keywords-section">
              <h3>Active Keywords</h3>
              <div className="keyword-chips">
                {keywords.map((kw) => (
                  <span className="keyword-chip" key={kw}>
                    {kw}
                    <button
                      className="remove-chip"
                      onClick={() => removeKeyword(kw)}
                      aria-label={`Remove ${kw}`}
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="filters-section">
            <h3>Filters</h3>
            <div className="filter-group">
              <label htmlFor="year-filter">Year Range</label>
              <select
                id="year-filter"
                value={yearFilter}
                onChange={(e) => setYearFilter(e.target.value)}
              >
                <option value="all">All Years</option>
                <option value="2024">2024</option>
                <option value="2023">2023</option>
                <option value="2020-2022">2020 – 2022</option>
                <option value="2015-2019">2015 – 2019</option>
                <option value="before-2015">Before 2015</option>
              </select>
            </div>
            <div className="filter-group">
              <label htmlFor="sort-by">Sort By</label>
              <select
                id="sort-by"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
              >
                <option value="relevance">Relevance</option>
                <option value="citations">Citations</option>
                <option value="year">Year (Newest)</option>
              </select>
            </div>
          </div>
        </div>
      </aside>

      {/* ===== RECOMMENDATIONS PANEL ===== */}
      <main className="glass-panel recommendations-panel" id="recommendations-panel">
        <div className="panel-header">
          <h2>
            <span className="icon">📄</span> Recommendations
          </h2>
          <p>Papers matching your search criteria</p>
        </div>

        <div className="panel-body">
          {hasSearched ? (
            <>
              <div className="results-count">
                Showing <span>{MOCK_PAPERS.length}</span> results
              </div>
              {MOCK_PAPERS.map((paper) => (
                <article className="paper-card" key={paper.id} id={`paper-${paper.id}`}>
                  <h3 className="paper-title">{paper.title}</h3>
                  <p className="paper-authors">{paper.authors}</p>
                  <p className="paper-abstract">{paper.abstract}</p>
                  <div className="paper-meta">
                    <span className="meta-tag citations">
                      📊 {formatNumber(paper.citations)} citations
                    </span>
                    <span className="meta-tag year">📅 {paper.year}</span>
                    <span className="meta-tag relevance">
                      ✨ {paper.relevance}% match
                    </span>
                  </div>
                </article>
              ))}
            </>
          ) : (
            <div className="empty-state">
              <div className="empty-icon">📚</div>
              <h3>No search yet</h3>
              <p>
                Enter keywords in the search panel to discover relevant research
                papers and citation recommendations.
              </p>
            </div>
          )}
        </div>
      </main>


    </div>
  );
};

export default HomePage;
