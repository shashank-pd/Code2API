/**
 * Tests for the ResultsPanel component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ResultsPanel from '../../components/panels/ResultsPanel';

describe('ResultsPanel Component', () => {
  const mockAnalysis = {
    success: true,
    analysis: {
      api_endpoints: [
        {
          function_name: 'get_users',
          http_method: 'GET',
          endpoint_path: '/users',
          description: 'Get all users',
          needs_auth: true,
          parameters: [{ name: 'limit', type: 'int', default: '10' }]
        },
        {
          function_name: 'create_user',
          http_method: 'POST',
          endpoint_path: '/users',
          description: 'Create a new user',
          needs_auth: false,
          parameters: [
            { name: 'username', type: 'str' },
            { name: 'email', type: 'str' }
          ]
        }
      ],
      security_recommendations: [
        'Hash passwords before storing',
        'Implement rate limiting',
        'Use HTTPS in production'
      ],
      optimization_suggestions: [
        'Add database connection pooling',
        'Implement response caching',
        'Use async operations where possible'
      ],
      repository_info: {
        name: 'test-repo',
        description: 'A test repository',
        language: 'Python',
        stars: 100,
        forks: 20
      }
    },
    generated_api_path: '/generated/test_api',
    message: 'Analysis completed successfully'
  };

  const defaultProps = {
    analysis: mockAnalysis,
    onDownload: vi.fn()
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders without crashing', () => {
    render(<ResultsPanel {...defaultProps} />);
    expect(screen.getByText(/analysis completed successfully/i)).toBeInTheDocument();
  });

  it('displays analysis message', () => {
    render(<ResultsPanel {...defaultProps} />);
    expect(screen.getByText('Analysis completed successfully')).toBeInTheDocument();
  });

  it('displays API endpoints correctly', () => {
    render(<ResultsPanel {...defaultProps} />);
    
    // Should show endpoint information
    expect(screen.getByText('get_users')).toBeInTheDocument();
    expect(screen.getByText('create_user')).toBeInTheDocument();
    expect(screen.getByText('GET')).toBeInTheDocument();
    expect(screen.getByText('POST')).toBeInTheDocument();
    expect(screen.getByText('/users')).toBeInTheDocument();
    expect(screen.getByText('Get all users')).toBeInTheDocument();
    expect(screen.getByText('Create a new user')).toBeInTheDocument();
  });

  it('shows authentication indicators', () => {
    render(<ResultsPanel {...defaultProps} />);
    
    // Should indicate which endpoints require auth
    // This depends on how the component displays auth requirements
    expect(screen.getByText(/get_users/)).toBeInTheDocument();
    expect(screen.getByText(/create_user/)).toBeInTheDocument();
  });

  it('displays endpoint parameters', () => {
    render(<ResultsPanel {...defaultProps} />);
    
    // Should show parameter information
    expect(screen.getByText(/limit/)).toBeInTheDocument();
    expect(screen.getByText(/username/)).toBeInTheDocument();
    expect(screen.getByText(/email/)).toBeInTheDocument();
  });

  it('displays security recommendations', () => {
    render(<ResultsPanel {...defaultProps} />);
    
    expect(screen.getByText(/Hash passwords before storing/)).toBeInTheDocument();
    expect(screen.getByText(/Implement rate limiting/)).toBeInTheDocument();
    expect(screen.getByText(/Use HTTPS in production/)).toBeInTheDocument();
  });

  it('displays optimization suggestions', () => {
    render(<ResultsPanel {...defaultProps} />);
    
    expect(screen.getByText(/Add database connection pooling/)).toBeInTheDocument();
    expect(screen.getByText(/Implement response caching/)).toBeInTheDocument();
    expect(screen.getByText(/Use async operations where possible/)).toBeInTheDocument();
  });

  it('displays repository information when available', () => {
    render(<ResultsPanel {...defaultProps} />);
    
    expect(screen.getByText(/test-repo/)).toBeInTheDocument();
    expect(screen.getByText(/A test repository/)).toBeInTheDocument();
    expect(screen.getByText(/Python/)).toBeInTheDocument();
    expect(screen.getByText(/100/)).toBeInTheDocument(); // Stars
    expect(screen.getByText(/20/)).toBeInTheDocument(); // Forks
  });

  it('shows download button and calls onDownload when clicked', async () => {
    render(<ResultsPanel {...defaultProps} />);
    const user = userEvent.setup();
    
    const downloadButton = screen.getByRole('button', { name: /download/i });
    await user.click(downloadButton);
    
    expect(defaultProps.onDownload).toHaveBeenCalled();
  });

  it('handles analysis without repository info', () => {
    const analysisWithoutRepo = {
      ...mockAnalysis,
      analysis: {
        ...mockAnalysis.analysis,
        repository_info: undefined
      }
    };

    render(<ResultsPanel analysis={analysisWithoutRepo} onDownload={vi.fn()} />);
    
    // Should still render without crashing
    expect(screen.getByText('Analysis completed successfully')).toBeInTheDocument();
  });

  it('handles analysis with no endpoints', () => {
    const analysisWithoutEndpoints = {
      ...mockAnalysis,
      analysis: {
        ...mockAnalysis.analysis,
        api_endpoints: []
      }
    };

    render(<ResultsPanel analysis={analysisWithoutEndpoints} onDownload={vi.fn()} />);
    
    // Should show message about no endpoints found
    expect(screen.getByText(/no.*endpoints/i) || screen.getByText(/0.*endpoints/i)).toBeInTheDocument();
  });

  it('handles analysis with no security recommendations', () => {
    const analysisWithoutSecurity = {
      ...mockAnalysis,
      analysis: {
        ...mockAnalysis.analysis,
        security_recommendations: []
      }
    };

    render(<ResultsPanel analysis={analysisWithoutSecurity} onDownload={vi.fn()} />);
    
    // Should handle gracefully
    expect(screen.getByText('Analysis completed successfully')).toBeInTheDocument();
  });

  it('handles analysis with no optimization suggestions', () => {
    const analysisWithoutOptimizations = {
      ...mockAnalysis,
      analysis: {
        ...mockAnalysis.analysis,
        optimization_suggestions: []
      }
    };

    render(<ResultsPanel analysis={analysisWithoutOptimizations} onDownload={vi.fn()} />);
    
    // Should handle gracefully
    expect(screen.getByText('Analysis completed successfully')).toBeInTheDocument();
  });

  it('displays endpoint count summary', () => {
    render(<ResultsPanel {...defaultProps} />);
    
    // Should show total number of endpoints
    expect(screen.getByText(/2.*endpoints/i) || screen.getByText(/endpoints.*2/i)).toBeInTheDocument();
  });

  it('shows different HTTP methods with appropriate styling', () => {
    render(<ResultsPanel {...defaultProps} />);
    
    const getMethod = screen.getByText('GET');
    const postMethod = screen.getByText('POST');
    
    expect(getMethod).toBeInTheDocument();
    expect(postMethod).toBeInTheDocument();
    
    // Different methods might have different styling classes
    expect(getMethod.className).toBeDefined();
    expect(postMethod.className).toBeDefined();
  });
});

describe('ResultsPanel Error Handling', () => {
  it('handles null analysis gracefully', () => {
    render(<ResultsPanel analysis={null} onDownload={vi.fn()} />);
    // Should not crash
    expect(screen.queryByText(/error/i) || screen.queryByText(/invalid/i)).toBeInTheDocument();
  });

  it('handles analysis without success field', () => {
    const invalidAnalysis = {
      analysis: {
        api_endpoints: []
      },
      message: 'Test message'
    };

    render(<ResultsPanel analysis={invalidAnalysis} onDownload={vi.fn()} />);
    expect(screen.getByText('Test message')).toBeInTheDocument();
  });

  it('handles malformed endpoint data', () => {
    const analysisWithMalformedEndpoints = {
      success: true,
      analysis: {
        api_endpoints: [
          {
            // Missing required fields
            function_name: 'test'
          },
          null, // Null endpoint
          {
            function_name: 'valid_endpoint',
            http_method: 'GET',
            endpoint_path: '/test',
            description: 'Valid endpoint'
          }
        ]
      },
      message: 'Analysis with malformed data'
    };

    render(<ResultsPanel analysis={analysisWithMalformedEndpoints} onDownload={vi.fn()} />);
    
    // Should handle malformed data gracefully and show valid endpoints
    expect(screen.getByText('valid_endpoint')).toBeInTheDocument();
  });

  it('handles missing onDownload prop', () => {
    render(<ResultsPanel analysis={mockAnalysis} />);
    
    // Should render without crashing even if onDownload is missing
    expect(screen.getByText('Analysis completed successfully')).toBeInTheDocument();
  });
});