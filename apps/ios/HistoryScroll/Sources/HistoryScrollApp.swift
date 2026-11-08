import SwiftUI

@main
struct HistoryScrollApp: App {
    var body: some Scene {
        WindowGroup {
            WebViewContainer()
                .preferredColorScheme(.light)
                .statusBarHidden(false)
        }
    }
}
