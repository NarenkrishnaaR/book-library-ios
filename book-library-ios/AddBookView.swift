//
//  AddBookView.swift
//  BookLibrary
//
//  Created by Naren on 27/03/25.
//

import SwiftUI
import SwiftData

struct AddBookView: View {
  @Environment(\.dismiss) private var dismiss
  @Environment(\.modelContext) private var context
  
  @State private var bookTitle = ""
  @State private var authorName = ""
  @State private var selectedYear = Calendar.current.component(.year, from: Date())
  @State private var selectedGenre: Book.BookGenre = .fiction
  @State private var isFavourite: Bool = false
  @State private var readingStatus: ReadingStatus = .currentRead
  
  var body: some View {
    NavigationStack {
      formView
        .navigationTitle("Add Book")
        .toolbar {
          ToolbarItem(placement: .topBarTrailing) {
            Button("Save") {
              DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
                saveData()
//                dismiss()
              }
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
      Picker("Status", selection: $readingStatus) {
        ForEach(ReadingStatus.allCases, id: \.self) { status in
          Text(status.rawValue).tag(status)
        }
      }
      .pickerStyle(.menu)
      Toggle("Favourite", isOn: $isFavourite)
    }
  }
  
  func saveData() {
    let newBook = Book(title: bookTitle,
                       authorName: authorName, publicationYear: 0,
                       genre:  selectedGenre,
                       isFavourite: isFavourite,
                       publishedYear: String(selectedYear))
    let fetchDescriptor = FetchDescriptor<Category>(predicate: #Predicate { $0.name == readingStatus.rawValue })
    do {
      if let existingCategory = try context.fetch(fetchDescriptor).first, existingCategory.name == readingStatus.rawValue {
        newBook.category = existingCategory
      } else {
        let category = Category(name: readingStatus.rawValue,
                                books: [newBook])
        category.books.append(newBook)
        newBook.category = category
        context.insert(category)
      }
    } catch {
      print("Failed to fetch categories: \(error)")
    }
    context.insert(newBook)
  }
}

#Preview {
  AddBookView()
}
