import '@testing-library/react';

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});

// Mock Element.prototype.scrollIntoView
Element.prototype.scrollIntoView = () => {};

// Mock HTMLCanvasElement.prototype.getContext for headless JSDOM WebGL tests
HTMLCanvasElement.prototype.getContext = function (this: HTMLCanvasElement, contextType: string) {
  if (contextType === 'webgl' || contextType === 'webgl2' || contextType === 'experimental-webgl') {
    return {
      canvas: this,
      drawingBufferWidth: 800,
      drawingBufferHeight: 600,
      getExtension: () => null,
      getParameter: () => 0,
      createTexture: () => ({}),
      bindTexture: () => {},
      texParameteri: () => {},
      texImage2D: () => {},
      clearColor: () => {},
      clearDepth: () => {},
      clear: () => {},
      enable: () => {},
      disable: () => {},
      depthFunc: () => {},
      frontFace: () => {},
      cullFace: () => {},
      viewport: () => {},
      createBuffer: () => ({}),
      bindBuffer: () => {},
      bufferData: () => {},
      createProgram: () => ({}),
      createShader: () => ({}),
      shaderSource: () => {},
      compileShader: () => {},
      getShaderParameter: () => true,
      attachShader: () => {},
      linkProgram: () => {},
      getProgramParameter: () => true,
      useProgram: () => {},
      getUniformLocation: () => ({}),
      getAttribLocation: () => 0,
      enableVertexAttribArray: () => {},
      vertexAttribPointer: () => {},
      drawArrays: () => {},
      drawElements: () => {},
      deleteTexture: () => {},
      deleteBuffer: () => {},
      deleteProgram: () => {},
      deleteShader: () => {},
    };
  }
  return null;
} as any;
