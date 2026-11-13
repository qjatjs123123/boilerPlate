// vitest.setup.ts — jsdom 에 없는 브라우저 API 보충 (shadcn/ui = Radix 부품이 사용)
// Radix Select 는 포인터 캡처·스크롤 API 를 호출하므로 jsdom 환경에서만 빈 구현을 채운다.
if (typeof window !== 'undefined' && typeof Element !== 'undefined') {
  Element.prototype.hasPointerCapture ??= () => false;
  Element.prototype.releasePointerCapture ??= () => {};
  Element.prototype.scrollIntoView ??= () => {};
}
