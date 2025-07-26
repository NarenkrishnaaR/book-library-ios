//
//  BookLibrary.swift
//  BookLibrary
//
//  Created by Naren on 26/03/25.
//

import SwiftUI
import SwiftData

@main
struct BookLibrary: App {
  var sharedModelContainer: ModelContainer = {
    let schema = Schema([
      Book.self, Category.self
    ])
    // Define custom database URL
    let dbURL = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)
      .first?
      .appendingPathComponent("BookLib.sqlite")
    let modelConfiguration = ModelConfiguration(schema: schema, url: dbURL!)
    
    do {
      return try ModelContainer(for: schema, configurations: [modelConfiguration])
    } catch {
      fatalError("Could not create ModelContainer: \(error)")
    }
  }()
  
  var body: some Scene {
    WindowGroup {
      BookListView()
    }
    .modelContainer(sharedModelContainer)
  }
}
