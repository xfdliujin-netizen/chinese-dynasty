import SwiftUI
import WebKit

/// 全屏铺满的 WebView 容器。
/// ignoresSafeArea 让内容延伸到状态栏与 Home 指示条之下，
/// 项目 CSS 里的 env(safe-area-inset-*) 会拿到真实数值并自行避让。
struct WebViewContainer: View {
    var body: some View {
        ShellWebView()
            .ignoresSafeArea(.all)
            .background(paper)
    }

    private var paper: Color {
        Color(red: 0.961, green: 0.941, blue: 0.902)
    }
}

struct ShellWebView: UIViewRepresentable {
    func makeCoordinator() -> Coordinator {
        Coordinator()
    }

    func makeUIView(context: Context) -> WKWebView {
        context.coordinator.webView
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}

    final class Coordinator {
        let webView: WKWebView

        init() {
            let cfg = WKWebViewConfiguration()
            // 本地资源通过 app:// scheme 提供，iframe / localStorage / fetch 行为与浏览器一致
            cfg.setURLSchemeHandler(AppSchemeHandler(), forURLScheme: "app")
            cfg.allowsInlineMediaPlayback = true
            cfg.mediaTypesRequiringUserActionForPlayback = []

            let wv = WKWebView(frame: .zero, configuration: cfg)
            wv.scrollView.bounces = false
            wv.scrollView.contentInsetAdjustmentBehavior = .never
            wv.allowsBackForwardNavigationGestures = false
            wv.isOpaque = false
            wv.backgroundColor = UIColor(red: 0.961, green: 0.941, blue: 0.902, alpha: 1)
            // native-shim.js 依据 UA 判断处于原生壳内
            let baseUA = wv.value(forKey: "userAgent") as? String ?? ""
            wv.customUserAgent = baseUA + " HistoryScrollApp/1.0"

            if let url = URL(string: "app://local/index.html") {
                wv.load(URLRequest(url: url))
            }
            self.webView = wv
        }
    }
}
