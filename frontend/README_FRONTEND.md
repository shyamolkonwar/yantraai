# Yantra AI Frontend

A modern, responsive Next.js application for the Yantra AI document processing platform. This frontend provides an intuitive interface for uploading documents, reviewing AI-extracted data, and managing processed files.

## Features

### Core Functionality
- **Document Upload**: Drag-and-drop PDF upload with progress tracking
- **Real-time Processing**: Live status updates as documents are processed
- **PDF Viewer**: Interactive PDF viewer with bounding box overlays
- **Field Review**: Visual field inspection with trust scoring
- **Human-in-the-Loop**: Fast keyboard-accelerated review queue
- **PII Redaction**: Preview and download redacted documents
- **Export Options**: JSON data export with confidence scores
- **Role-Based Access**: Different interfaces for uploaders, reviewers, and admins

### User Experience
- **Trust Score Visualization**: Color-coded trust badges with detailed breakdowns
- **Keyboard Shortcuts**: Power user controls for fast review workflows
- **Responsive Design**: Works seamlessly on desktop and mobile
- **Accessibility**: WCAG compliant with proper focus management
- **Animations**: Smooth micro-interactions and page transitions
- **Real-time Updates**: Live polling for job status changes

## Technology Stack

- **Framework**: Next.js 15 with TypeScript
- **Styling**: Tailwind CSS with custom design system
- **State Management**: Zustand for global state, React Query for server state
- **Animations**: Framer Motion for smooth interactions
- **Icons**: Lucide React for consistent iconography
- **Forms**: React Hook Form with Zod validation
- **HTTP Client**: Axios with interceptors for authentication

## Getting Started

### Prerequisites
- Node.js 18+ and npm
- Yantra AI backend running (see ../backend/README.md)

### Installation

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
```bash
cp .env.local.example .env.local
# Edit .env.local with your backend URL
```

3. Start the development server:
```bash
npm run dev
```

4. Open http://localhost:3000 in your browser

## Environment Variables

```bash
# Backend API URL (required)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Environment (development, staging, production)
NEXT_PUBLIC_ENV=development

# Feature flags
NEXT_PUBLIC_ENABLE_ANALYTICS=false
NEXT_PUBLIC_ENABLE_SENTRY=false
```

## Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── (auth)/             # Authentication routes
│   ├── dashboard/          # Main dashboard
│   ├── jobs/[id]/          # Job detail pages
│   └── review/             # Review queue
├── components/
│   ├── ui/                  # Reusable UI components
│   ├── pages/              # Page-level components
│   └── providers/          # React providers
├── lib/                    # Utilities and API client
├── stores/                 # Zustand state stores
└── types/                  # TypeScript type definitions
```

## Key Components

### PDF Viewer (`/components/ui/pdf-viewer.tsx`)
- Interactive PDF display with zoom controls
- Bounding box overlays for extracted regions
- PII redaction preview toggle
- Page navigation and zoom controls

### Trust Score Badge (`/components/ui/trust-score-badge.tsx`)
- Visual trust score indicators
- Color-coded confidence levels (high/medium/low)
- Detailed tooltips with confidence breakdown
- Animated appearance and state changes

### Field List (`/components/ui/field-list.tsx`)
- Virtualized list of extracted fields
- Search and filtering capabilities
- Trust score statistics
- Field editing and verification indicators

### Upload Area (`/components/ui/upload-area.tsx`)
- Drag-and-drop file upload interface
- Progress tracking and error handling
- File validation and size limits
- Animated upload feedback

## Authentication Flow

1. **Login**: JWT-based authentication with role management
2. **Authorization**: Role-gated access to different features
3. **Session Management**: Secure token storage and refresh
4. **Auto-redirect**: Protected routes redirect to login

## API Integration

The frontend integrates seamlessly with the Yantra AI backend:

- **REST API**: All backend endpoints are properly typed
- **Error Handling**: Comprehensive error mapping and user feedback
- **Optimistic Updates**: Immediate UI feedback with rollback on errors
- **Polling**: Real-time status updates for job processing
- **File Uploads**: Multipart form data with progress tracking

## Performance Optimizations

- **Code Splitting**: Route-based and component-based lazy loading
- **Virtualization**: Efficient rendering for large field lists
- **Image Optimization**: Responsive images and lazy loading
- **Bundle Analysis**: Optimized for production builds
- **Caching**: React Query caching for API responses

## Accessibility

- **Keyboard Navigation**: Full keyboard accessibility
- **Screen Reader Support**: Proper ARIA labels and landmarks
- **Focus Management**: Logical tab order and focus indicators
- **Color Contrast**: WCAG AA compliant color combinations
- **Reduced Motion**: Respects user motion preferences

## Development

### Code Style
- TypeScript for type safety
- ESLint for code quality
- Prettier for formatting
- Consistent naming conventions
- Comprehensive type definitions

### Testing Strategy
- Component unit tests with React Testing Library
- Integration tests for API interactions
- E2E tests for critical user flows
- Accessibility testing with axe-core

### Build Process
```bash
# Development
npm run dev

# Build for production
npm run build

# Start production server
npm run start

# Run linter
npm run lint
```

## Design System

### Brand Colors
- **Primary**: #0F6FFF (Electric Indigo)
- **Success**: #16A34A (Green)
- **Warning**: #F59E0B (Amber)
- **Danger**: #EF4444 (Red)
- **Background**: #FAFBFE (Off-white)

### Typography
- **Font**: Inter for body, JetBrains Mono for code
- **Sizes**: Responsive scale from mobile to desktop
- **Weights**: Medium for headings, Regular for body text

### Animation Principles
- **Purposeful**: Motion should clarify function
- **Fast**: Quick for micro-interactions (90-180ms)
- **Polite**: Slower for context changes (300-450ms)
- **Consistent**: Single easing curve family

## Deployment

### Vercel (Recommended)
1. Connect GitHub repository to Vercel
2. Configure environment variables
3. Automatic deployment on push to main

### Docker
```bash
# Build Docker image
docker build -t yantra-ai-frontend .

# Run container
docker run -p 3000:3000 yantra-ai-frontend
```

### Manual Deployment
```bash
# Build for production
npm run build

# Start production server
npm run start
```

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the documentation at `/docs`
- Review the API documentation at `/docs/api`
- Open an issue for bugs or feature requests

---

Built with ❤️ for the Yantra AI document processing platform