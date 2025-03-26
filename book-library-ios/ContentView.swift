//
//  ContentView.swift
//  book-library-ios
//
//  Created by Naren on 26/03/25.
//

import SwiftUI
import SwiftData

struct ContentView: View {
  
  var body: some View {
    EmptyView()
  }
}

#Preview {
  ContentView()
    .modelContainer(for: Book.self, inMemory: true)
}
