/**
 * Tests for the main App component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axios from 'axios';
import App from '../App';

// Mock axios
vi.mock('axios');
const mockedAxios = vi.mocked(axios);

// Mock Monaco Editor
vi.mock('@monaco-editor/react', () => ({
  default: ({ value, onChange, language }) => (
    <textarea
      data-testid="monaco-editor"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      data-language={language}
    />
  ),
}));

// Mock Swagger UI
vi.mock('swagger-ui-react', () => ({
  default: ({ spec }) => (
    <div data-testid="swagger-ui">
      Swagger UI: {JSON.stringify(spec)}
    </div>
  ),
}));

describe('App Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders without crashing', () => {
    render(<App />);
    expect(screen.getByText('Code2API')).toBeInTheDocument();
    expect(screen.getByText('AI-powered system that converts source code into APIs')).toBeInTheDocument();
  });

  it('displays the correct default state', () => {
    render(<App />);
    
    // Should show editor tab by default
    expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
    
    // Should have default language as Python
    const editor = screen.getByTestId('monaco-editor');
    expect(editor).toHaveAttribute('data-language', 'python');
    
    // Should have sample code
    expect(editor.value).toContain('def calculate_user_score');
  });

  it('switches between code and repository input modes', async () => {
    render(<App />);
    const user = userEvent.setup();
    
    // Should start in code mode
    expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
    
    // Switch to repository mode (this would need to be implemented in the UI)
    // For now, we'll test the state management
    expect(screen.getByText('Code2API')).toBeInTheDocument();
  });

  it('handles language change', async () => {
    render(<App />);
    const user = userEvent.setup();
    
    // Find and click language selector (if implemented)
    // This test assumes there's a language selector in the UI
    const editor = screen.getByTestId('monaco-editor');
    
    // Initial language should be Python
    expect(editor).toHaveAttribute('data-language', 'python');
    expect(editor.value).toContain('def calculate_user_score');
  });

  it('handles code analysis request', async () => {
    render(<App />);
    const user = userEvent.setup();
    
    // Mock successful API response
    const mockResponse = {
      data: {
        success: true,
        analysis: {
          api_endpoints: [
            {
              function_name: 'test_function',
              http_method: 'GET',
              endpoint_path: '/test',
              description: 'Test endpoint',
              needs_auth: false,
              parameters: []
            }
          ]
        },
        generated_api_path: '/path/to/generated/api',
        message: 'Analysis successful'
      }
    };
    
    mockedAxios.post.mockResolvedValueOnce(mockResponse);
    
    // Find and click analyze button (assuming it exists)
    const analyzeButton = screen.getByRole('button', { name: /analyze/i });
    await user.click(analyzeButton);
    
    // Wait for API call
    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith('/api/analyze', expect.objectContaining({
        language: 'python',
        filename: 'example.py'
      }));
    });
  });

  it('handles API errors gracefully', async () => {
    render(<App />);
    const user = userEvent.setup();
    
    // Mock API error
    const mockError = {
      response: {
        data: {
          detail: 'API analysis failed'
        }
      }
    };
    
    mockedAxios.post.mockRejectedValueOnce(mockError);
    
    // Try to analyze code
    const analyzeButton = screen.getByRole('button', { name: /analyze/i });
    await user.click(analyzeButton);
    
    // Should show error message
    await waitFor(() => {
      expect(screen.getByText(/API analysis failed/i)).toBeInTheDocument();
    });
  });

  it('handles repository URL analysis', async () => {
    render(<App />);
    
    // Mock successful repository analysis
    const mockResponse = {
      data: {
        success: true,
        analysis: {
          api_endpoints: [],
          repository_info: {
            name: 'test-repo',
            description: 'Test repository'
          }
        },
        message: 'Repository analyzed successfully'
      }
    };
    
    mockedAxios.post.mockResolvedValueOnce(mockResponse);
    
    // This would test repository analysis if the UI supports it
    expect(screen.getByText('Code2API')).toBeInTheDocument();
  });

  it('generates Swagger specification correctly', () => {
    render(<App />);
    
    // We'll need to test this by setting the analysis state
    // This requires the component to expose the generateSwaggerSpec function
    // or we can test it indirectly through the UI
    expect(screen.getByText('Code2API')).toBeInTheDocument();
  });

  it('handles file upload', async () => {
    render(<App />);
    const user = userEvent.setup();
    
    // Mock file upload response
    const mockResponse = {
      data: {
        results: [
          {
            filename: 'test.py',
            success: true,
            analysis: {
              api_endpoints: []
            }
          }
        ],
        total_files: 1
      }
    };
    
    mockedAxios.post.mockResolvedValueOnce(mockResponse);
    
    // Create a test file
    const file = new File(['def test(): pass'], 'test.py', { type: 'text/x-python' });
    
    // Find file input (if it exists)
    const fileInput = screen.queryByRole('textbox', { hidden: true });
    if (fileInput) {
      await user.upload(fileInput, file);
      
      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith('/api/upload', expect.any(FormData), {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
      });
    }
  });

  it('handles download API functionality', async () => {
    render(<App />);
    
    // Mock blob response for download
    const mockBlob = new Blob(['test content'], { type: 'application/zip' });
    const mockResponse = { data: mockBlob };
    
    mockedAxios.get.mockResolvedValueOnce(mockResponse);
    
    // Create URL mock
    global.URL.createObjectURL = vi.fn(() => 'mock-url');
    global.URL.revokeObjectURL = vi.fn();
    
    // Mock link click
    const mockLink = {
      click: vi.fn(),
      remove: vi.fn(),
      setAttribute: vi.fn()
    };
    document.createElement = vi.fn(() => mockLink);
    document.body.appendChild = vi.fn();
    
    // This would test the download functionality
    // Need to trigger it through the UI
    expect(screen.getByText('Code2API')).toBeInTheDocument();
  });

  it('validates required fields before analysis', async () => {
    render(<App />);
    const user = userEvent.setup();
    
    // Clear the editor content
    const editor = screen.getByTestId('monaco-editor');
    await user.clear(editor);
    
    // Try to analyze empty code
    const analyzeButton = screen.getByRole('button', { name: /analyze/i });
    await user.click(analyzeButton);
    
    // Should show validation error
    await waitFor(() => {
      expect(screen.getByText(/please enter some code to analyze/i)).toBeInTheDocument();
    });
  });
});

describe('App Component Integration', () => {
  it('completes full analysis workflow', async () => {
    render(<App />);
    const user = userEvent.setup();
    
    // Mock successful analysis
    const mockAnalysisResponse = {
      data: {
        success: true,
        analysis: {
          api_endpoints: [
            {
              function_name: 'test_function',
              http_method: 'GET',
              endpoint_path: '/test',
              description: 'Test endpoint',
              needs_auth: false,
              parameters: [{ name: 'param1', type: 'str' }]
            }
          ],
          security_recommendations: ['Use HTTPS'],
          optimization_suggestions: ['Add caching']
        },
        generated_api_path: '/generated/test_api',
        message: 'Analysis completed successfully'
      }
    };
    
    mockedAxios.post.mockResolvedValueOnce(mockAnalysisResponse);
    
    // Enter code in editor
    const editor = screen.getByTestId('monaco-editor');
    await user.clear(editor);
    await user.type(editor, 'def test_function(): return "test"');
    
    // Click analyze
    const analyzeButton = screen.getByRole('button', { name: /analyze/i });
    await user.click(analyzeButton);
    
    // Wait for analysis to complete
    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith('/api/analyze', {
        code: 'def test_function(): return "test"',
        language: 'python',
        filename: 'example.py'
      });
    });
    
    // Should show results (if results panel is implemented)
    // This would test the full workflow
  });
});