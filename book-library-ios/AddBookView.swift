//
//  AddBookView.swift
//  BookLibrary
//
//  Created by Naren on 27/03/25.
//

import SwiftUI

struct AddBookView: View {
  @Environment(\.dismiss) private var dismiss
  @Environment(\.modelContext) private var modelContext
  
  @State private var bookTitle = ""
  @State private var authorName = ""
  @State private var selectedYear = Calendar.current.component(.year, from: Date())
  @State private var selectedGenre: Book.BookGenre = .fiction
  @State private var isFavourite: Bool = false
  
  var body: some View {
    NavigationStack {
      formView
        .navigationTitle("Add Book")
        .toolbar {
          ToolbarItem(placement: .topBarTrailing) {
            Button("Save") {
              saveData()
              dismiss()
            }
          }
        }
    }
  }
  
  var formView: some View {
    Form {
      TextField("Title", text: $bookTitle)
      Picker("Genre", selection: $selectedGenre) {
        ForEach(Book.BookGenre.allCases, id: \.self) { genre in
          Text(genre.rawValue).tag(genre)
            .background(selectedGenre == genre ? Color.blue.opacity(0.3) : Color.clear)
        }
      }
      .pickerStyle(.segmented)
      TextField("Author Name", text: $authorName)
      Picker("Publication Year", selection: $selectedYear) {
        ForEach((1900...Calendar.current.component(.year, from: Date())).reversed(), id: \.self) { year in
          Text(String(year)).tag(year)
        }
      }
      Toggle("Favourite", isOn: $isFavourite)
    }
  }
  
  func saveData() {
    let newBook = Book(title: bookTitle,
                       authorName: authorName, publicationYear: 0,
                       genre:  selectedGenre,
                       isFavourite: isFavourite,
                       publishedYear: String(selectedYear))
    modelContext.insert(newBook)
  }
}

#Preview {
  AddBookView()
}
