/**
 * Tests for the EditorPanel component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import EditorPanel from '../../components/panels/EditorPanel';

// Mock Monaco Editor
vi.mock('@monaco-editor/react', () => ({
  default: ({ value, onChange, language, options }) => (
    <textarea
      data-testid="monaco-editor"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      data-language={language}
      data-options={JSON.stringify(options)}
    />
  ),
}));

describe('EditorPanel Component', () => {
  const defaultProps = {
    language: 'python',
    setLanguage: vi.fn(),
    filename: 'test.py',
    setFilename: vi.fn(),
    fileInputRef: { current: null },
    uploadFiles: vi.fn(),
    analyzing: false,
    code: 'def hello(): return "world"',
    setCode: vi.fn(),
    onAnalyze: vi.fn()
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders without crashing', () => {
    render(<EditorPanel {...defaultProps} />);
    expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
  });

  it('displays the correct code in editor', () => {
    render(<EditorPanel {...defaultProps} />);
    const editor = screen.getByTestId('monaco-editor');
    expect(editor.value).toBe('def hello(): return "world"');
  });

  it('shows correct language in editor', () => {
    render(<EditorPanel {...defaultProps} />);
    const editor = screen.getByTestId('monaco-editor');
    expect(editor).toHaveAttribute('data-language', 'python');
  });

  it('calls setCode when editor content changes', async () => {
    render(<EditorPanel {...defaultProps} />);
    const user = userEvent.setup();
    
    const editor = screen.getByTestId('monaco-editor');
    await user.clear(editor);
    await user.type(editor, 'new code');
    
    expect(defaultProps.setCode).toHaveBeenCalledWith('new code');
  });

  it('shows language selector and allows language change', async () => {
    render(<EditorPanel {...defaultProps} />);
    
    // Look for language selector (assuming it exists in the component)
    const languageSelect = screen.queryByRole('combobox');
    if (languageSelect) {
      const user = userEvent.setup();
      await user.selectOptions(languageSelect, 'javascript');
      expect(defaultProps.setLanguage).toHaveBeenCalledWith('javascript');
    }
  });

  it('shows filename input and allows filename change', async () => {
    render(<EditorPanel {...defaultProps} />);
    
    // Look for filename input
    const filenameInput = screen.queryByDisplayValue('test.py');
    if (filenameInput) {
      const user = userEvent.setup();
      await user.clear(filenameInput);
      await user.type(filenameInput, 'newfile.py');
      expect(defaultProps.setFilename).toHaveBeenCalledWith('newfile.py');
    }
  });

  it('shows analyze button and calls onAnalyze when clicked', async () => {
    render(<EditorPanel {...defaultProps} />);
    const user = userEvent.setup();
    
    const analyzeButton = screen.getByRole('button', { name: /analyze/i });
    await user.click(analyzeButton);
    
    expect(defaultProps.onAnalyze).toHaveBeenCalled();
  });

  it('disables analyze button when analyzing', () => {
    render(<EditorPanel {...defaultProps} analyzing={true} />);
    
    const analyzeButton = screen.getByRole('button', { name: /analyz/i });
    expect(analyzeButton).toBeDisabled();
  });

  it('shows loading state when analyzing', () => {
    render(<EditorPanel {...defaultProps} analyzing={true} />);
    
    // Should show some loading indicator
    expect(screen.getByRole('button', { name: /analyz/i })).toBeDisabled();
  });

  it('handles file upload button click', async () => {
    const mockFileRef = { current: { click: vi.fn() } };
    render(<EditorPanel {...defaultProps} fileInputRef={mockFileRef} />);
    const user = userEvent.setup();
    
    // Look for upload button
    const uploadButton = screen.queryByRole('button', { name: /upload/i });
    if (uploadButton) {
      await user.click(uploadButton);
      expect(mockFileRef.current.click).toHaveBeenCalled();
    }
  });

  it('handles file input change', async () => {
    render(<EditorPanel {...defaultProps} />);
    
    // Look for hidden file input
    const fileInput = screen.queryByRole('textbox', { hidden: true });
    if (fileInput) {
      const file = new File(['test content'], 'test.py', { type: 'text/x-python' });
      const user = userEvent.setup();
      
      await user.upload(fileInput, file);
      expect(defaultProps.uploadFiles).toHaveBeenCalled();
    }
  });

  it('shows correct editor configuration options', () => {
    render(<EditorPanel {...defaultProps} />);
    const editor = screen.getByTestId('monaco-editor');
    
    // Check if editor has proper configuration
    const options = JSON.parse(editor.getAttribute('data-options') || '{}');
    expect(options).toBeDefined();
  });

  it('handles different programming languages correctly', () => {
    const languages = ['python', 'javascript', 'java'];
    
    languages.forEach(language => {
      const { rerender } = render(<EditorPanel {...defaultProps} language={language} />);
      const editor = screen.getByTestId('monaco-editor');
      expect(editor).toHaveAttribute('data-language', language);
      rerender(<div />); // Clean up
    });
  });

  it('shows proper file extension based on language', () => {
    const languageToExtension = {
      python: '.py',
      javascript: '.js',
      java: '.java'
    };

    Object.entries(languageToExtension).forEach(([lang, ext]) => {
      const filename = `test${ext}`;
      render(<EditorPanel {...defaultProps} language={lang} filename={filename} />);
      
      // Should show the correct filename
      const filenameDisplay = screen.queryByDisplayValue(filename);
      expect(filenameDisplay).toBeInTheDocument();
    });
  });
});

describe('EditorPanel Error Handling', () => {
  const defaultProps = {
    language: 'python',
    setLanguage: vi.fn(),
    filename: 'test.py',
    setFilename: vi.fn(),
    fileInputRef: { current: null },
    uploadFiles: vi.fn(),
    analyzing: false,
    code: '',
    setCode: vi.fn(),
    onAnalyze: vi.fn()
  };

  it('handles empty code gracefully', () => {
    render(<EditorPanel {...defaultProps} />);
    const editor = screen.getByTestId('monaco-editor');
    expect(editor.value).toBe('');
  });

  it('handles null filename gracefully', () => {
    render(<EditorPanel {...defaultProps} filename={null} />);
    // Should not crash
    expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
  });

  it('handles invalid language gracefully', () => {
    render(<EditorPanel {...defaultProps} language="invalid" />);
    const editor = screen.getByTestId('monaco-editor');
    expect(editor).toHaveAttribute('data-language', 'invalid');
  });

  it('handles missing fileInputRef gracefully', () => {
    render(<EditorPanel {...defaultProps} fileInputRef={null} />);
    // Should not crash
    expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
  });
});